#!/usr/bin/env python3
"""
LLM 기반 결정사항 추출 테스트
"""
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.agenda_analysis_agent import AgendaAnalysisAgent
from config.settings import settings

def test_llm_extraction():
    """LLM 기반 결정사항 추출 테스트"""
    print("🧪 LLM 기반 결정사항 추출 테스트")
    print("=" * 50)
    
    # API 키 확인
    if not settings.upstage_api_key and not settings.openai_api_key:
        print("❌ API 키가 설정되지 않았습니다.")
        print("   .env 파일에 UPSTAGE_API_KEY 또는 OPENAI_API_KEY를 설정해주세요.")
        return
    
    # 테스트 발언들
    test_utterances = [
        "프로젝트 일정을 3개월로 연장하는 것에 대해 찬성합니다. 감사드립니다.",
        "팀 조직을 개편하여 개발팀과 기획팀을 통합하겠습니다.",
        "새로운 시스템 개발을 시작하겠습니다. 이 결정사항에 대해서는 모든 참가자분들의 동의를 받아서 진행하겠습니다.",
        "예산을 20% 증가시키는 것에 동의합니다.",
        "다음 주 월요일부터 원격 근무를 시행하겠습니다.",
        "그냥 일반적인 대화입니다. 특별한 결정사항은 없어요.",
        "품질 관리 시스템을 도입하여 테스트 프로세스를 개선하겠습니다. 이 결정사항의 실행을 위해서는 구체적인 실행 계획과 일정을 수립해야 하고, 성공적인 실행을 위해 최선을 다하겠습니다."
    ]
    
    agent = AgendaAnalysisAgent()
    
    print(f"🔑 API 설정:")
    print(f"   Upstage API: {'✅' if settings.upstage_api_key else '❌'}")
    print(f"   OpenAI API: {'✅' if settings.openai_api_key else '❌'}")
    print()
    
    for i, utterance in enumerate(test_utterances, 1):
        print(f"📝 테스트 {i}:")
        print(f"   원본: {utterance}")
        
        # LLM 기반 추출
        decision = agent._extract_decision_content(utterance)
        
        print(f"   추출: {decision if decision else '(결정사항 없음)'}")
        print()
    
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    test_llm_extraction() 