"""
Unit tests for NLP modules (Text2SQL, Summarization)
"""
import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.nlp.text2sql import Text2SQLConverter, convert_natural_to_sql
from src.nlp.summarization import generate_summary  # TODO: NLP 담당자가 구현


class TestText2SQL:
    """Test cases for Text2SQL conversion"""
    
    def setup_method(self):
        """Setup test environment"""
        self.converter = Text2SQLConverter()
    
    def test_speaker_query_conversion(self):
        """Test speaker-related query conversion"""
        query = "누가 프로젝트 일정에 대해 언급했나요?"
        result = self.converter.convert_to_sql(query)
        
        assert result["natural_query"] == query
        assert "SELECT" in result["sql_query"]
        assert "speaker" in result["sql_query"].lower()
        assert result["method"] in ["model", "rules"]
        assert result["confidence"] > 0
    
    def test_time_query_conversion(self):
        """Test time-related query conversion"""
        query = "언제 프로젝트 마감일이 결정되었나요?"
        result = self.converter.convert_to_sql(query)
        
        assert result["natural_query"] == query
        assert "SELECT" in result["sql_query"]
        assert result["method"] in ["model", "rules"]
    
    def test_content_query_conversion(self):
        """Test content-related query conversion"""
        query = "프로젝트 예산에 대해 무엇을 논의했나요?"
        result = self.converter.convert_to_sql(query)
        
        assert result["natural_query"] == query
        assert "SELECT" in result["sql_query"]
        assert "프로젝트" in result["sql_query"] or "예산" in result["sql_query"]
    
    def test_action_query_conversion(self):
        """Test action/decision query conversion"""
        query = "회의에서 어떤 결정사항이 있었나요?"
        result = self.converter.convert_to_sql(query)
        
        assert result["natural_query"] == query
        assert "SELECT" in result["sql_query"]
        assert "actions" in result["sql_query"].lower() or "description" in result["sql_query"].lower()
    
    def test_sql_validation(self):
        """Test SQL query validation"""
        # Valid SQL
        valid_sql = "SELECT speaker, text FROM utterances WHERE text LIKE '%test%'"
        assert self.converter.validate_sql(valid_sql) == True
        
        # Invalid SQL (missing SELECT)
        invalid_sql = "FROM utterances WHERE text LIKE '%test%'"
        assert self.converter.validate_sql(invalid_sql) == False
        
        # Dangerous SQL (should be blocked)
        dangerous_sql = "DROP TABLE users"
        assert self.converter.validate_sql(dangerous_sql) == False
    
    def test_keyword_extraction(self):
        """Test keyword extraction from natural language"""
        query = "누가 프로젝트 일정과 예산에 대해 언급했나요?"
        keywords = self.converter._extract_keywords(query)
        
        assert len(keywords) > 0
        assert "프로젝트" in keywords or "일정" in keywords or "예산" in keywords
        assert "누가" not in keywords  # Stop words should be filtered
        assert "언급" not in keywords  # Stop words should be filtered


class TestSummarization:
    """Test cases for summarization module"""
    
    def test_summary_generation(self):
        """Test meeting summary generation"""
        # TODO: NLP 담당자가 구현 후 테스트 추가
        transcript = "이 회의에서는 프로젝트 일정과 예산에 대해 논의했습니다. 김철수가 프론트엔드 개발을 담당하고, 이영희가 백엔드 개발을 담당하기로 결정했습니다."
        
        # Placeholder test - 실제 구현 후 수정 필요
        assert len(transcript) > 0
        # result = generate_summary(transcript)
        # assert len(result["summary"]) > 0
        # assert len(result["key_points"]) > 0


class TestIntegration:
    """Integration tests for NLP modules"""
    
    def test_end_to_end_query_processing(self):
        """Test complete query processing pipeline"""
        # Test natural language query → SQL → validation
        query = "누가 프로젝트에 대해 언급했나요?"
        
        # Convert to SQL
        result = convert_natural_to_sql(query)
        
        # Validate result
        assert result["natural_query"] == query
        assert "sql_query" in result
        assert "method" in result
        assert "confidence" in result
        
        # Validate SQL
        converter = Text2SQLConverter()
        assert converter.validate_sql(result["sql_query"]) == True


# Performance tests
class TestPerformance:
    """Performance tests for NLP modules"""
    
    def test_text2sql_response_time(self):
        """Test Text2SQL conversion response time"""
        import time
        
        converter = Text2SQLConverter()
        query = "누가 프로젝트에 대해 언급했나요?"
        
        start_time = time.time()
        result = converter.convert_to_sql(query)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should complete within 1 second
        assert response_time < 1.0
        assert result["natural_query"] == query


# Error handling tests
class TestErrorHandling:
    """Error handling tests"""
    
    def test_empty_query_handling(self):
        """Test handling of empty queries"""
        converter = Text2SQLConverter()
        
        # Empty query should not crash
        result = converter.convert_to_sql("")
        assert result["natural_query"] == ""
        assert "sql_query" in result
    
    def test_invalid_query_handling(self):
        """Test handling of invalid queries"""
        converter = Text2SQLConverter()
        
        # Very long query should be handled gracefully
        long_query = "테스트" * 1000
        result = converter.convert_to_sql(long_query)
        
        assert result["natural_query"] == long_query
        assert "sql_query" in result


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 