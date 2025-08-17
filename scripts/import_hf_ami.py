import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from datasets import load_dataset
from src.database.models import Meeting, Utterance
from config.database import get_postgresql_session, create_tables
from collections import defaultdict


def _pick_key(sample_row, candidates):
	"""Return the first existing key from candidates based on sample row."""
	for key in candidates:
		if key in sample_row and sample_row[key] is not None:
			return key
	return None


# 1. 데이터셋 로드 (처음 N개 샘플만)
print("[INFO] Loading samples from Huggingface AMI dataset...")
ds = load_dataset("edinburghcstr/ami", "ihm", split="train[:10000]")

# 1-1. 필드 자동 매핑 (샘플 1건 기반)
sample = ds[0] if len(ds) > 0 else {}
print(f"[INFO] Sample keys: {list(sample.keys())}")

meeting_key = _pick_key(sample, ["meeting_id", "dialogue_id", "session_id", "meeting", "id"])
speaker_key = _pick_key(sample, ["speaker", "speaker_id", "participant", "speaker_name", "role"])
text_key = _pick_key(sample, ["text", "transcript", "utterance", "sentence"])
start_key = _pick_key(sample, ["begin_time", "start_time", "start", "offset", "timestamp"]) 
end_key = _pick_key(sample, ["end_time", "stop_time", "end", "time_end"]) 

if not meeting_key:
	raise RuntimeError("Could not detect meeting id field in AMI dataset. Checked: meeting_id/dialogue_id/session_id/meeting/id")
if not text_key:
	raise RuntimeError("Could not detect text field in AMI dataset. Checked: text/transcript/utterance/sentence")

print("[INFO] Detected field mapping:")
print(f"  meeting_key = {meeting_key}")
print(f"  speaker_key = {speaker_key or 'N/A (will default to Unknown)'}")
print(f"  text_key    = {text_key}")
print(f"  start_key   = {start_key or 'N/A (will default to 0.0)'}")
print(f"  end_key     = {end_key or 'N/A (optional)'}")

# 2. 테이블 생성 보장
print("[INFO] Ensuring database tables exist...")
create_tables()

# 3. DB 세션 열기
print("[INFO] Connecting to database...")
db = get_postgresql_session()

# 4. 미팅별로 그룹핑 및 participants 추출
grouped = defaultdict(list)
participants = defaultdict(set)
for row in ds:
	m_id = row.get(meeting_key)
	if m_id is None:
		# 스킵 (비정상 레코드)
		continue
	grouped[m_id].append(row)
	spk = row.get(speaker_key) if speaker_key else None
	if spk is not None:
		participants[m_id].add(str(spk))
	else:
		# 스피커 키가 없으면 Unknown으로 처리 (중복 방지 위해 고정 문자열)
		participants[m_id].add("Unknown")

# 5. Meeting/Utterance 적재 (idempotent)
meeting_objs = {}
for m_id, utter_list in grouped.items():
	# get-or-create Meeting by title
	existing_meeting = db.query(Meeting).filter(Meeting.title == str(m_id)).first()
	if existing_meeting:
		meeting = existing_meeting
		# participants 병합
		existing_participants = set(meeting.participants or [])
		new_participants = existing_participants.union(participants[m_id])
		if new_participants != existing_participants:
			meeting.participants = list(new_participants)
			db.add(meeting)
	else:
		meeting = Meeting(
			title=str(m_id),
			date=None,  # 날짜 정보 없음
			participants=list(participants[m_id]),
			summary="",
		)
		db.add(meeting)
		db.flush()  # id 확보
		meeting_objs[m_id] = meeting

	# utterances upsert-like: (meeting_id, timestamp, text) 존재 시 스킵
	inserted = 0
	skipped = 0
	for row in utter_list:
		start_ts = row.get(start_key, 0.0) if start_key else 0.0
		end_ts = row.get(end_key) if end_key and end_key in row else None
		text_val = str(row.get(text_key, ""))
		exists = (
			db.query(Utterance.id)
			.filter(Utterance.meeting_id == meeting.id)
			.filter(Utterance.timestamp == (float(start_ts) if start_ts is not None else 0.0))
			.filter(Utterance.text == text_val)
			.first()
		)
		if exists:
			skipped += 1
			continue
		utt = Utterance(
			meeting_id=meeting.id,
			speaker=str(row.get(speaker_key, "Unknown")) if speaker_key else "Unknown",
			timestamp=float(start_ts) if start_ts is not None else 0.0,
			end_timestamp=float(end_ts) if end_ts is not None else None,
			text=text_val,
		)
		db.add(utt)
		inserted += 1
	# 배치 커밋
	db.commit()
	print(f"[INFO] Meeting {meeting.title}: inserted={inserted}, skipped={skipped}")

print("✅ Huggingface AMI 샘플 데이터 적재 완료 (idempotent)")
db.close()
