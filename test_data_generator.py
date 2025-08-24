"""
가상 회의 데이터 생성기 - 멀티에이전트 분석 테스트용
"""
import requests
import json
from datetime import datetime, timedelta
import random
import time

# API 설정
API_BASE_URL = "http://localhost:8000/api/v1"

def generate_test_meeting_data():
    """가상의 회의 데이터 생성"""
    
    # 회의 제목들
    meeting_titles = [
        "2024년 1분기 프로젝트 기획 회의",
        "신제품 출시 전략 논의",
        "팀 조직 개편 안건 검토",
        "예산 계획 및 리소스 할당",
        "고객 피드백 분석 및 개선 방안"
    ]
    
    # 화자들
    speakers = ["김팀장", "이과장", "박대리", "최사원", "정부장"]
    
    # 회의 주제별 키워드
    topic_keywords = {
        "프로젝트": ["일정", "마감", "진행상황", "리스크", "계획", "목표", "성과"],
        "예산": ["비용", "투자", "절약", "수익", "ROI", "예산안", "재정"],
        "인사": ["조직", "인력", "채용", "평가", "승진", "교육", "팀워크"],
        "기술": ["개발", "시스템", "플랫폼", "기술력", "혁신", "디지털", "AI"],
        "마케팅": ["고객", "시장", "전략", "브랜드", "홍보", "판매", "경쟁"]
    }
    
    # 회의 내용 템플릿
    meeting_templates = [
        {
            "title": "2024년 1분기 프로젝트 기획 회의",
            "duration": 45,
            "speakers": ["김팀장", "이과장", "박대리"],
            "topics": ["프로젝트", "일정", "예산"],
            "decisions": [
                "프로젝트 A는 3월 말까지 완료하기로 결정",
                "예산 5천만원 추가 할당 승인",
                "주간 진행상황 보고 체계 구축"
            ]
        },
        {
            "title": "신제품 출시 전략 논의",
            "duration": 60,
            "speakers": ["정부장", "김팀장", "이과장", "최사원"],
            "topics": ["마케팅", "기술", "예산"],
            "decisions": [
                "신제품 출시일을 4월 15일로 확정",
                "마케팅 예산 2억원 배정",
                "베타 테스트 2주간 진행"
            ]
        },
        {
            "title": "팀 조직 개편 안건 검토",
            "duration": 30,
            "speakers": ["정부장", "김팀장", "이과장"],
            "topics": ["인사", "조직"],
            "decisions": [
                "개발팀과 기획팀 통합 검토",
                "신규 인력 3명 채용 계획 수립",
                "조직도 개편안 다음 주까지 완성"
            ]
        }
    ]
    
    return meeting_templates

def generate_utterances(meeting_template):
    """회의 템플릿을 기반으로 발화 데이터 생성"""
    utterances = []
    current_time = 0
    speaker_idx = 0
    
    # 회의 시작
    start_utterance = {
        "speaker": meeting_template["speakers"][0],
        "timestamp": current_time,
        "end_timestamp": current_time + 15,
        "text": f"안녕하세요. 오늘 {meeting_template['title']}를 시작하겠습니다. 먼저 안건을 확인해보겠습니다. 오늘 논의할 주요 사항들을 정리해서 말씀드리겠습니다."
    }
    utterances.append(start_utterance)
    current_time += 20
    
    # 주제별 논의
    for topic in meeting_template["topics"]:
        # 주제 소개
        intro_text = f"다음은 {topic} 관련 안건입니다. "
        if topic == "프로젝트":
            intro_text += "현재 진행 중인 프로젝트들의 상황을 점검하고 앞으로의 계획을 논의해보겠습니다. 특히 일정 관리와 리스크 대응 방안에 대해 중점적으로 검토하겠습니다."
        elif topic == "예산":
            intro_text += "예산 현황을 파악하고 추가 투자가 필요한 부분을 검토해보겠습니다. 투자 대비 효과와 비용 효율성을 종합적으로 분석해보겠습니다."
        elif topic == "인사":
            intro_text += "조직 개편과 인력 배치에 대해 의견을 나누어보겠습니다. 현재 조직의 효율성과 향후 발전 방향을 고려해서 논의하겠습니다."
        elif topic == "기술":
            intro_text += "기술 개발 현황과 향후 방향성을 논의해보겠습니다. 최신 기술 트렌드와 우리 회사의 기술 경쟁력을 점검해보겠습니다."
        elif topic == "마케팅":
            intro_text += "마케팅 전략과 고객 반응에 대해 분석해보겠습니다. 시장 상황과 경쟁사 동향을 파악하고 효과적인 마케팅 방안을 모색해보겠습니다."
        
        utterances.append({
            "speaker": meeting_template["speakers"][speaker_idx % len(meeting_template["speakers"])],
            "timestamp": current_time,
            "end_timestamp": current_time + 12,
            "text": intro_text
        })
        current_time += 18
        speaker_idx += 1
        
        # 각 화자별 의견
        for i, speaker in enumerate(meeting_template["speakers"]):
            # 화자별 특성에 따른 발화 생성
            if speaker == "김팀장":
                opinion_text = f"저는 {topic}에 대해 체계적인 접근이 필요하다고 생각합니다. "
                if topic == "프로젝트":
                    opinion_text += "일정 관리와 리스크 대응 방안을 우선적으로 검토해야겠습니다. 현재 진행 중인 프로젝트들의 마일스톤을 점검하고, 지연 가능성이 있는 부분들을 미리 파악해서 대응 방안을 마련해야 할 것 같습니다. 특히 외부 의존성이 높은 작업들에 대해서는 백업 플랜을 준비하는 것이 중요하겠습니다."
                elif topic == "예산":
                    opinion_text += "투자 대비 효과를 정량적으로 분석해서 결정하는 것이 좋겠습니다. 각 프로젝트별 ROI를 계산하고, 우선순위를 정해서 예산을 배분하는 것이 효율적일 것 같습니다. 또한 예상치 못한 비용이 발생할 수 있는 부분들에 대해서도 충분한 여유 자금을 확보해두는 것이 필요하겠습니다."
                elif topic == "인사":
                    opinion_text += "조직의 효율성을 높이기 위해서는 명확한 역할 분담과 책임 소재를 정하는 것이 중요합니다. 현재 중복되는 업무나 소통이 원활하지 않은 부분들을 개선하고, 각 팀원의 강점을 살릴 수 있는 배치를 고려해야겠습니다."
                elif topic == "기술":
                    opinion_text += "기술 개발의 방향성을 명확히 하고, 단계별 목표를 설정해서 체계적으로 진행해야겠습니다. 최신 기술 트렌드를 파악하면서도 우리 회사의 실정에 맞는 기술을 선택하는 것이 중요하고, 개발 인력의 역량 강화도 함께 고려해야겠습니다."
                elif topic == "마케팅":
                    opinion_text += "마케팅 전략을 수립할 때는 타겟 고객을 명확히 정의하고, 그들의 니즈를 정확히 파악하는 것이 중요합니다. 경쟁사와의 차별화 포인트를 찾아서 브랜드 아이덴티티를 강화하고, 다양한 채널을 활용한 통합 마케팅 커뮤니케이션을 구축해야겠습니다."
            elif speaker == "이과장":
                opinion_text = f"{topic} 관련해서 실무적인 관점에서 말씀드리면, "
                if topic == "프로젝트":
                    opinion_text += "현재 팀원들의 업무 부담이 상당히 높은 상황입니다. 일정이 너무 타이트하게 잡혀있어서 품질 관리에 어려움이 있을 수 있고, 팀원들의 피로도도 높아지고 있습니다. 현실적인 일정 조정과 인력 보강이 필요할 것 같습니다."
                elif topic == "예산":
                    opinion_text += "현재 예산으로는 계획된 일정을 맞추기 어려울 것 같습니다. 특히 외부 업체 의존도가 높은 부분들에서 예상보다 많은 비용이 발생하고 있고, 장비나 소프트웨어 라이선스 비용도 계속 증가하고 있습니다. 예산 증액이나 우선순위 재조정이 필요하겠습니다."
                elif topic == "인사":
                    opinion_text += "현재 조직에서 소통이 원활하지 않은 부분들이 있습니다. 팀 간 협업이 필요한 프로젝트에서 정보 공유가 제대로 되지 않아서 중복 작업이나 혼선이 발생하고 있고, 업무 프로세스도 개선이 필요한 상황입니다. 조직 개편과 함께 업무 프로세스 개선도 함께 진행해야겠습니다."
                elif topic == "기술":
                    opinion_text += "기술 개발 현장에서는 최신 기술 도입에 대한 부담감이 있습니다. 새로운 기술을 학습하는 시간이 필요하고, 기존 시스템과의 호환성 문제도 고려해야 합니다. 단계적인 도입과 충분한 교육 시간을 확보하는 것이 중요하겠습니다."
                elif topic == "마케팅":
                    opinion_text += "현재 마케팅 활동에서 고객 반응을 정확히 측정하기 어려운 부분들이 있습니다. 다양한 채널을 사용하고 있지만 통합적인 분석이 부족하고, 고객 피드백을 수집하고 분석하는 시스템도 개선이 필요합니다. 데이터 기반의 마케팅 의사결정을 위해서는 분석 도구와 프로세스 개선이 시급합니다."
            elif speaker == "박대리":
                opinion_text = f"제가 {topic}에 대해 조사한 내용을 공유드리겠습니다. "
                if topic == "프로젝트":
                    opinion_text += "시장 동향을 보면 경쟁사들이 비슷한 프로젝트를 진행하고 있습니다. 특히 A사와 B사는 이미 유사한 서비스를 출시했고, C사도 개발 중인 것으로 파악됩니다. 우리가 차별화할 수 있는 포인트를 찾아서 경쟁 우위를 확보해야겠습니다. 또한 고객 인터뷰 결과, 사용자들이 가장 중요하게 생각하는 기능들을 파악했는데, 이를 반영한 개발 방향 조정이 필요할 것 같습니다."
                elif topic == "예산":
                    opinion_text += "외부 벤치마킹 결과, 우리보다 20% 더 많은 예산을 투입하고 있습니다. 특히 기술 개발과 마케팅 영역에서 차이가 크고, 인력 투입도 더 적극적입니다. 하지만 예산 효율성 측면에서는 우리가 더 우수한 것으로 나타났습니다. 적절한 예산 증액과 함께 효율성 유지 방안을 모색해야겠습니다."
                elif topic == "인사":
                    opinion_text += "업계 평균과 비교했을 때 우리 회사의 조직 효율성은 양호한 수준입니다. 하지만 개선 여지가 있는 부분들도 발견했는데, 특히 의사결정 속도와 정보 공유 측면에서 개선이 필요합니다. 다른 회사들의 사례를 참고해서 조직 문화 개선 방안을 제안드리겠습니다."
                elif topic == "기술":
                    opinion_text += "최신 기술 트렌드를 분석한 결과, AI와 클라우드 기술이 핵심이 되고 있습니다. 우리 회사도 이 분야에 투자를 확대해야겠지만, 단계적 접근이 필요합니다. 특히 AI 기술 도입 시 데이터 품질과 보안 문제를 해결하는 것이 우선이 되어야겠습니다."
                elif topic == "마케팅":
                    opinion_text += "고객 설문조사와 시장 분석 결과, 디지털 마케팅 채널의 중요성이 계속 증가하고 있습니다. 특히 소셜미디어와 콘텐츠 마케팅에서 효과가 높게 나타났고, 개인화된 마케팅 메시지에 대한 고객 반응도 좋습니다. 이 분야에 대한 투자를 확대하고 전문 인력 확보가 필요하겠습니다."
            elif speaker == "최사원":
                opinion_text = f"{topic}에 대해 제 의견을 말씀드리면, "
                if topic == "프로젝트":
                    opinion_text += "사용자 관점에서 더 편리한 기능이 필요할 것 같습니다. 현재 개발 중인 기능들이 기술적으로는 훌륭하지만, 실제 사용자들이 사용하기에는 복잡한 부분들이 있습니다. 사용자 경험을 개선하고 직관적인 인터페이스를 제공하는 것이 중요하겠습니다. 또한 모바일 환경에서의 사용성도 크게 개선이 필요합니다."
                elif topic == "예산":
                    opinion_text += "고객 만족도 향상을 위한 추가 투자가 필요하다고 생각합니다. 현재 서비스 품질은 양호하지만, 고객들이 요구하는 추가 기능들이 많이 있습니다. 특히 고객 지원 시스템 개선과 사용자 교육 자료 개발에 투자하면 고객 만족도가 크게 향상될 것으로 예상됩니다."
                elif topic == "인사":
                    opinion_text += "젊은 세대의 관점에서 보면, 업무 환경의 유연성이 중요합니다. 재택근무나 유연근무제 도입을 고려해보시는 것이 어떨까요? 또한 업무와 개인 생활의 균형을 위한 제도 개선도 필요하고, 젊은 인재들이 선호하는 업무 문화를 만들어가는 것이 중요하겠습니다."
                elif topic == "기술":
                    opinion_text += "최신 기술에 대한 학습 기회를 더 많이 제공해주시면 좋겠습니다. 기술 발전이 빠르기 때문에 지속적인 학습이 필요하고, 특히 젊은 개발자들이 새로운 기술을 배우고 적용할 수 있는 환경을 만들어주시면 회사의 기술 경쟁력이 크게 향상될 것 같습니다."
                elif topic == "마케팅":
                    opinion_text += "젊은 고객층을 대상으로 한 마케팅 전략이 부족하다고 생각합니다. 현재 마케팅이 주로 기존 고객층에 집중되어 있는데, 새로운 세대의 고객들을 유치하기 위해서는 그들이 선호하는 채널과 메시지를 활용해야겠습니다. 특히 소셜미디어와 인플루언서 마케팅에 대한 투자를 확대하는 것이 효과적일 것 같습니다."
            elif speaker == "정부장":
                opinion_text = f"{topic}에 대한 전략적 관점에서 말씀드리겠습니다. "
                if topic == "프로젝트":
                    opinion_text += "장기적인 비전과 연계해서 접근해야 할 것 같습니다. 현재 진행 중인 프로젝트들이 단기적인 성과에만 집중되어 있는 경향이 있는데, 회사의 장기 발전 방향과 연계해서 프로젝트의 우선순위를 재조정해야겠습니다. 또한 지속 가능한 성장을 위한 기반 구축에도 투자해야겠습니다."
                elif topic == "예산":
                    opinion_text += "회사의 전체적인 재정 상황을 고려해서 결정해야겠습니다. 현재 경제 상황이 불안정하고, 향후 예측하기 어려운 요소들이 많기 때문에 보수적인 접근이 필요합니다. 하지만 성장을 위한 투자는 계속해야 하므로, 리스크를 최소화하면서도 효과적인 투자를 할 수 있는 방안을 모색해야겠습니다."
                elif topic == "인사":
                    opinion_text += "조직의 장기적 경쟁력을 위해서는 인재 육성과 조직 문화 개선이 핵심입니다. 현재 인력의 역량 강화를 위한 교육 투자를 확대하고, 창의적이고 혁신적인 조직 문화를 만들어가는 것이 중요하겠습니다. 또한 미래 인재 확보를 위한 채용 전략도 함께 수립해야겠습니다."
                elif topic == "기술":
                    opinion_text += "기술은 회사의 핵심 경쟁력이므로 장기적인 관점에서 투자해야겠습니다. 단기적인 성과보다는 지속 가능한 기술 발전을 위한 기반 구축에 집중하고, 혁신적인 기술 개발을 통해 시장에서의 우위를 확보해야겠습니다. 또한 기술 윤리와 사회적 책임도 함께 고려해야겠습니다."
                elif topic == "마케팅":
                    opinion_text += "마케팅은 단순한 판매 도구가 아니라 브랜드 가치를 높이는 전략적 도구로 접근해야겠습니다. 장기적인 브랜드 빌딩과 고객과의 신뢰 관계 구축에 집중하고, 지속 가능한 성장을 위한 마케팅 전략을 수립해야겠습니다. 또한 사회적 가치를 추구하는 마케팅으로 차별화해야겠습니다."
            
            utterances.append({
                "speaker": speaker,
                "timestamp": current_time,
                "end_timestamp": current_time + 20,
                "text": opinion_text
            })
            current_time += 25
            
            # 다른 화자들의 반응
            if i < len(meeting_template["speakers"]) - 1:
                next_speaker = meeting_template["speakers"][(i + 1) % len(meeting_template["speakers"])]
                response_text = f"네, {speaker}님 말씀이 맞습니다. "
                if random.random() > 0.5:
                    response_text += "추가로 보완할 점이 있다면 "
                    if topic == "프로젝트":
                        response_text += "품질 관리 방안도 함께 고려해야겠습니다. 현재 개발 과정에서 품질 검증이 부족한 부분들이 있어서, 체계적인 테스트 프로세스와 품질 관리 시스템을 구축하는 것이 필요하겠습니다. 또한 사용자 피드백을 반영한 지속적인 개선 방안도 마련해야겠습니다."
                    elif topic == "예산":
                        response_text += "비용 효율성 측면도 검토가 필요합니다. 현재 일부 비용이 비효율적으로 사용되고 있는 부분들이 있어서, 비용 분석을 통한 최적화 방안을 찾아야겠습니다. 또한 투자 대비 효과를 정기적으로 측정하고 평가하는 시스템도 구축해야겠습니다."
                    elif topic == "인사":
                        response_text += "조직 문화 개선도 함께 진행해야겠습니다. 현재 업무 환경에서 개선이 필요한 부분들이 있어서, 직원들이 더 만족할 수 있는 근무 환경을 만들어가는 것이 중요하겠습니다. 또한 성과 평가 시스템의 개선도 고려해야겠습니다."
                    elif topic == "기술":
                        response_text += "기술 윤리와 보안 측면도 고려해야겠습니다. 최신 기술 도입 시 발생할 수 있는 윤리적 문제와 보안 위험을 미리 파악하고 대응 방안을 마련해야겠습니다. 또한 기술 격차 해소를 위한 교육 프로그램도 필요하겠습니다."
                    elif topic == "마케팅":
                        response_text += "고객 데이터 보호와 개인정보 보안 측면도 중요합니다. 마케팅 활동에서 수집하는 고객 정보의 안전한 관리와 개인정보 보호를 위한 시스템 구축이 필요하겠습니다. 또한 투명하고 윤리적인 마케팅 활동을 위한 가이드라인도 마련해야겠습니다."
                else:
                    response_text += "그 부분에 대해 더 자세히 논의해보겠습니다. "
                    if topic == "프로젝트":
                        response_text += "특히 일정 관리와 리스크 대응 방안에 대해서는 구체적인 실행 계획을 수립해야겠고, 팀원들의 업무 부담 분산 방안도 함께 검토해야겠습니다."
                    elif topic == "예산":
                        response_text += "예산 배분의 우선순위를 정하고, 투자 대비 효과를 측정할 수 있는 지표들을 설정해야겠습니다. 또한 예상치 못한 비용 발생에 대비한 대응 방안도 마련해야겠습니다."
                    elif topic == "인사":
                        response_text += "조직 개편의 구체적인 방안과 일정을 정하고, 직원들의 의견을 수렴하는 과정을 거쳐야겠습니다. 또한 개편 후 발생할 수 있는 문제점들을 미리 파악하고 대응 방안을 준비해야겠습니다."
                    elif topic == "기술":
                        response_text += "기술 개발의 단계별 목표와 일정을 정하고, 필요한 인력과 예산을 산정해야겠습니다. 또한 기술 도입 시 발생할 수 있는 문제점들을 미리 파악하고 대응 방안을 마련해야겠습니다."
                    elif topic == "마케팅":
                        response_text += "마케팅 전략의 구체적인 실행 계획을 수립하고, 효과를 측정할 수 있는 지표들을 설정해야겠습니다. 또한 고객 반응을 실시간으로 모니터링할 수 있는 시스템도 구축해야겠습니다."
                
                utterances.append({
                    "speaker": next_speaker,
                    "timestamp": current_time,
                    "end_timestamp": current_time + 15,
                    "text": response_text
                })
                current_time += 20
    
    # 결정사항 발표
    for i, decision in enumerate(meeting_template["decisions"]):
        decision_text = f"그럼 {i+1}번째 안건에 대해 결정사항을 정리하겠습니다. {decision} 이 결정사항에 대해서는 모든 참가자분들의 동의를 받아서 진행하겠습니다. 이 결정사항의 실행을 위해서는 구체적인 실행 계획과 일정을 수립해야 하고, 정기적인 진행 상황 점검도 필요하겠습니다."
        utterances.append({
            "speaker": meeting_template["speakers"][0],  # 회의 진행자
            "timestamp": current_time,
            "end_timestamp": current_time + 15,
            "text": decision_text
        })
        current_time += 20
        
        # 동의 표시
        for speaker in meeting_template["speakers"][1:]:
            agreement_text = f"네, 동의합니다. {decision}에 대해 찬성합니다. 이 결정사항이 회사의 발전에 도움이 될 것이라고 생각하고, 성공적인 실행을 위해 최선을 다하겠습니다."
            utterances.append({
                "speaker": speaker,
                "timestamp": current_time,
                "end_timestamp": current_time + 10,
                "text": agreement_text
            })
            current_time += 15
    
    # 회의 마무리
    end_text = f"오늘 {meeting_template['title']}를 마무리하겠습니다. 결정된 사항들을 잘 실행해주시기 바랍니다. 다음 주에 진행 상황을 점검하는 회의를 가질 예정이니, 각자 담당 업무를 잘 수행해주시기 바랍니다. 오늘 참석해주신 모든 분들께 감사드립니다."
    utterances.append({
        "speaker": meeting_template["speakers"][0],
        "timestamp": current_time,
        "end_timestamp": current_time + 15,
        "text": end_text
    })
    
    return utterances

def create_test_meeting(meeting_template):
    """테스트 회의 데이터를 API를 통해 생성"""
    
    # 회의 기본 정보
    meeting_data = {
        "title": meeting_template["title"],
        "meeting_date": datetime.now().strftime("%Y-%m-%d"),
        "participants": meeting_template["speakers"]
    }
    
    # 발화 데이터 생성
    utterances = generate_utterances(meeting_template)
    
    print(f"📋 회의 생성 중: {meeting_template['title']}")
    print(f"👥 참가자: {', '.join(meeting_template['speakers'])}")
    print(f"⏱️ 예상 시간: {meeting_template['duration']}분")
    print(f"💬 총 발화 수: {len(utterances)}")
    print(f"🎯 결정사항: {len(meeting_template['decisions'])}개")
    print("-" * 50)
    
    # 실제로는 API를 통해 회의를 생성하고 발화 데이터를 저장해야 하지만,
    # 여기서는 테스트용으로 콘솔에 출력
    return {
        "meeting_data": meeting_data,
        "utterances": utterances
    }

def main():
    """메인 실행 함수"""
    print("🤖 가상 회의 데이터 생성기")
    print("=" * 50)
    
    # 테스트 회의 템플릿 생성
    meeting_templates = generate_test_meeting_data()
    
    # 각 회의별로 데이터 생성
    for i, template in enumerate(meeting_templates, 1):
        print(f"\n📊 회의 {i} 생성 중...")
        test_data = create_test_meeting(template)
        
        # 발화 데이터 샘플 출력
        print("\n💬 발화 데이터 샘플:")
        for j, utterance in enumerate(test_data["utterances"][:5]):  # 처음 5개만 출력
            print(f"  {j+1}. [{utterance['speaker']}] {utterance['text'][:50]}...")
        
        if len(test_data["utterances"]) > 5:
            print(f"  ... 및 {len(test_data['utterances']) - 5}개의 추가 발화")
        
        print("\n" + "="*50)
    
    print("\n✅ 가상 회의 데이터 생성 완료!")
    print("\n💡 다음 단계:")
    print("1. 이 데이터를 실제 데이터베이스에 저장")
    print("2. 멀티에이전트 분석 기능 테스트")
    print("3. 프론트엔드에서 결과 확인")

if __name__ == "__main__":
    main() 