<<<<<<< HEAD
"""
PDF generation utilities for meeting summaries
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import urllib.request
import io


class PDFGenerator:
    """PDF generation for meeting summaries"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_korean_font()
        self._setup_custom_styles()
    
    def _setup_korean_font(self):
        """Setup Korean font support with actual Korean TTF fonts"""
        try:
            # Create fonts directory if it doesn't exist
            fonts_dir = os.path.join("temp", "fonts")
            os.makedirs(fonts_dir, exist_ok=True)
            
            # Download and register Noto Sans CJK KR (Korean support)
            try:
                self._download_and_register_noto_font(fonts_dir)
                print("Noto Sans CJK KR fonts registered successfully")
            except Exception as e:
                print(f"Noto font download failed: {e}")
                # Try to use system fonts or embedded fonts
                try:
                    self._try_system_korean_fonts()
                    print("System Korean fonts registered")
                except Exception as e2:
                    print(f"System font registration failed: {e2}")
                    # Ultimate fallback - use DejaVu Sans which has better Unicode support
                    self._setup_unicode_fallback()
                    print("Using Unicode fallback fonts")
                    
        except Exception as e:
            print(f"Font setup failed completely: {e}")
            self.korean_font = 'Helvetica'
            self.korean_font_bold = 'Helvetica-Bold'
    
    def _download_and_register_noto_font(self, fonts_dir):
        """Download and register Noto Sans CJK Korean font"""
        # Use Google Fonts API for Noto Sans KR (web fonts)
        font_urls = {
            'NotoSansKR-Regular': 'https://fonts.gstatic.com/s/notosanskr/v27/PbykFmXiEBPT4ITbgNA5Cgm20HTs4JMMuA.woff2',
            'NotoSansKR-Bold': 'https://fonts.gstatic.com/s/notosanskr/v27/PbykFmXiEBPT4ITbgNA5Cgm20HTs4JMMuA.woff2'
        }
        
        # For now, skip download and use alternative approach
        raise Exception("Font download not implemented - using fallback")
    
    def _try_system_korean_fonts(self):
        """Try to register system Korean fonts with better options"""
        # Windows system fonts - try multiple options (prioritize modern fonts)
        windows_fonts = [
            # Modern fonts first
            ('C:/Windows/Fonts/NanumSquareR.ttf', 'NanumSquare'),
            ('C:/Windows/Fonts/NanumSquareB.ttf', 'NanumSquare-Bold'),
            ('C:/Windows/Fonts/NanumGothic.ttf', 'NanumGothic'),
            ('C:/Windows/Fonts/NanumGothicBold.ttf', 'NanumGothic-Bold'),
            ('C:/Windows/Fonts/NanumBarunGothic.ttf', 'NanumBarunGothic'),
            ('C:/Windows/Fonts/NanumBarunGothicBold.ttf', 'NanumBarunGothic-Bold'),
            # Fallback to system fonts
            ('C:/Windows/Fonts/malgun.ttf', 'MalgunGothic'),
            ('C:/Windows/Fonts/malgunbd.ttf', 'MalgunGothic-Bold'),
            ('C:/Windows/Fonts/gulim.ttc', 'Gulim'),
            ('C:/Windows/Fonts/gulim.ttc', 'Gulim-Bold'),
            ('C:/Windows/Fonts/batang.ttc', 'Batang'),
            ('C:/Windows/Fonts/batang.ttc', 'Batang-Bold'),
            ('C:/Windows/Fonts/dotum.ttc', 'Dotum'),
            ('C:/Windows/Fonts/dotum.ttc', 'Dotum-Bold')
        ]
        
        # Try to register both regular and bold versions
        registered_fonts = []
        
        for font_path, font_name in windows_fonts:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    registered_fonts.append(font_name)
                    print(f"Successfully registered: {font_name}")
                except Exception as e:
                    print(f"Failed to register {font_name}: {e}")
                    continue
        
        # Set the best available fonts (prioritize modern fonts)
        if 'NanumSquare' in registered_fonts:
            self.korean_font = 'NanumSquare'
            self.korean_font_bold = 'NanumSquare-Bold' if 'NanumSquare-Bold' in registered_fonts else 'NanumSquare'
        elif 'NanumGothic' in registered_fonts:
            self.korean_font = 'NanumGothic'
            self.korean_font_bold = 'NanumGothic-Bold' if 'NanumGothic-Bold' in registered_fonts else 'NanumGothic'
        elif 'NanumBarunGothic' in registered_fonts:
            self.korean_font = 'NanumBarunGothic'
            self.korean_font_bold = 'NanumBarunGothic-Bold' if 'NanumBarunGothic-Bold' in registered_fonts else 'NanumBarunGothic'
        elif 'MalgunGothic' in registered_fonts:
            self.korean_font = 'MalgunGothic'
            self.korean_font_bold = 'MalgunGothic-Bold' if 'MalgunGothic-Bold' in registered_fonts else 'MalgunGothic'
        elif 'Gulim' in registered_fonts:
            self.korean_font = 'Gulim'
            self.korean_font_bold = 'Gulim-Bold' if 'Gulim-Bold' in registered_fonts else 'Gulim'
        elif 'Dotum' in registered_fonts:
            self.korean_font = 'Dotum'
            self.korean_font_bold = 'Dotum-Bold' if 'Dotum-Bold' in registered_fonts else 'Dotum'
        elif 'Batang' in registered_fonts:
            self.korean_font = 'Batang'
            self.korean_font_bold = 'Batang-Bold' if 'Batang-Bold' in registered_fonts else 'Batang'
        else:
            raise Exception("No suitable Korean fonts found")
        
        print(f"Using fonts: {self.korean_font} (regular), {self.korean_font_bold} (bold)")
    
    def _setup_unicode_fallback(self):
        """Setup fonts with better Unicode support"""
        try:
            # Try DejaVu fonts which have better Unicode coverage
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            
            # Try different CID fonts with better Korean support
            korean_cid_fonts = [
                'Adobe-Korea1-UniKS-UTF32-H',
                'Adobe-Korea1-2', 
                'KozMinPro-Regular-Acro',
                'HeiseiKakuGo-W5',
                'HeiseiMin-W3'
            ]
            
            for font_name in korean_cid_fonts:
                try:
                    pdfmetrics.registerFont(UnicodeCIDFont(font_name))
                    self.korean_font = font_name
                    self.korean_font_bold = font_name
                    print(f"Successfully registered CID font: {font_name}")
                    return
                except Exception as e:
                    print(f"Failed to register {font_name}: {e}")
                    continue
            
            # If all CID fonts fail, use basic fonts
            self.korean_font = 'Helvetica'
            self.korean_font_bold = 'Helvetica-Bold'
            
        except Exception as e:
            print(f"Unicode fallback setup failed: {e}")
            self.korean_font = 'Helvetica'
            self.korean_font_bold = 'Helvetica-Bold'
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles with modern design"""
        # Modern color palette
        primary_color = colors.HexColor('#2563eb')  # Blue
        secondary_color = colors.HexColor('#64748b')  # Slate
        accent_color = colors.HexColor('#f59e0b')  # Amber
        text_dark = colors.HexColor('#1e293b')  # Dark slate
        text_light = colors.HexColor('#64748b')  # Light slate
        bg_light = colors.HexColor('#f8fafc')  # Light gray
        border_color = colors.HexColor('#e2e8f0')  # Border gray
        
        # Title style - clean and modern (reduced size)
        self.title_style = ParagraphStyle(
            'ModernTitle',
            parent=self.styles['Title'],
            fontSize=20,
            textColor=primary_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=15,
            fontName=getattr(self, 'korean_font_bold', 'Helvetica-Bold'),
            leading=24
        )
        
        # Section heading style - clean and modern (reduced size)
        self.heading_style = ParagraphStyle(
            'ModernHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=text_dark,
            spaceBefore=20,
            spaceAfter=12,
            leftIndent=0,
            fontName=getattr(self, 'korean_font_bold', 'Helvetica-Bold'),
            leading=18,
            borderWidth=0,
            borderColor=accent_color,
            borderPadding=5
        )
        
        # Body text style - readable and clean
        self.body_style = ParagraphStyle(
            'ModernBody',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=text_dark,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leftIndent=0,
            fontName=getattr(self, 'korean_font', 'Helvetica'),
            leading=16,
            firstLineIndent=0
        )
        
        # List item style - for numbered/bulleted lists
        self.list_style = ParagraphStyle(
            'ModernList',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=text_dark,
            alignment=TA_LEFT,
            spaceAfter=8,
            leftIndent=20,
            fontName=getattr(self, 'korean_font', 'Helvetica'),
            leading=16,
            firstLineIndent=-15,
            bulletIndent=15
        )
        
        # Meta info style - subtle and small
        self.meta_style = ParagraphStyle(
            'ModernMeta',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=text_light,
            spaceAfter=6,
            fontName=getattr(self, 'korean_font', 'Helvetica'),
            leading=14
        )
        
        # Quote style - for highlighted content
        self.quote_style = ParagraphStyle(
            'ModernQuote',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=text_dark,
            alignment=TA_LEFT,
            spaceAfter=10,
            leftIndent=20,
            rightIndent=20,
            fontName=getattr(self, 'korean_font', 'Helvetica'),
            leading=15,
            borderWidth=1,
            borderColor=border_color,
            borderPadding=10,
            backColor=bg_light
        )
        
        # Store colors for use in tables
        self.colors = {
            'primary': primary_color,
            'secondary': secondary_color,
            'accent': accent_color,
            'text_dark': text_dark,
            'text_light': text_light,
            'bg_light': bg_light,
            'border': border_color
        }
    
    def _create_time_ranges(self, utterances: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
        """
        Create time-based outline from utterances
        
        Args:
            utterances: List of utterance dictionaries
            
        Returns:
            List of (time_range, count) tuples
        """
        if not utterances:
            return []
        
        # Extract timestamps and convert to minutes
        timestamps = []
        for utterance in utterances:
            timestamp = utterance.get('timestamp', 0)
            try:
                timestamp_float = float(timestamp)
                timestamps.append(timestamp_float / 60)  # Convert to minutes
            except:
                timestamps.append(0)
        
        if not timestamps:
            return []
        
        # Find min and max time
        min_time = min(timestamps)
        max_time = max(timestamps)
        
        # Create 5-minute intervals
        intervals = []
        current_time = min_time
        interval_size = 5  # 5 minutes
        
        while current_time <= max_time:
            end_time = current_time + interval_size
            count = sum(1 for t in timestamps if current_time <= t < end_time)
            
            if count > 0:
                start_str = f"{int(current_time):02d}:{int((current_time % 1) * 60):02d}"
                end_str = f"{int(end_time):02d}:{int((end_time % 1) * 60):02d}"
                time_range = f"{start_str} - {end_str}"
                intervals.append((time_range, count))
            
            current_time = end_time
        
        return intervals

    def _add_time_info_to_summary(self, summary_text: str, utterances: List[Dict[str, Any]]) -> str:
        """
        Add time information to numbered summary points
        
        Args:
            summary_text: Original summary text with numbered points
            utterances: List of utterances with timestamps
            
        Returns:
            Summary text with time information added
        """
        if not summary_text or not utterances:
            return summary_text
        
        import re
        
        # Extract numbered points from summary
        numbered_points = re.findall(r'(\d+\.\s*\*\*[^*]+\*\*:.*?)(?=\d+\.\s*\*\*|\Z)', summary_text, re.DOTALL)
        
        if not numbered_points:
            return summary_text
        
        # Create keyword mapping for each numbered point
        point_keywords = []
        for i, point in enumerate(numbered_points, 1):
            # Extract keywords from the point title
            title_match = re.search(r'\d+\.\s*\*\*([^*]+)\*\*:', point)
            if title_match:
                title = title_match.group(1)
                # Extract key terms from title
                keywords = re.findall(r'[가-힣a-zA-Z]+', title)
                point_keywords.append((i, keywords, point))
        
        # Find time ranges for each point based on keyword matching
        enhanced_summary = summary_text
        for point_num, keywords, original_point in point_keywords:
            time_range = self._find_time_range_for_keywords(keywords, utterances)
            if time_range:
                # Add time information to the point
                time_info = f" <i>({time_range})</i>"
                enhanced_point = original_point.replace('**:', f'**:{time_info}')
                enhanced_summary = enhanced_summary.replace(original_point, enhanced_point)
        
        return enhanced_summary

    def _find_time_range_for_keywords(self, keywords: List[str], utterances: List[Dict[str, Any]]) -> str:
        """
        Find time range where keywords are most frequently mentioned
        
        Args:
            keywords: List of keywords to search for
            utterances: List of utterances with timestamps
            
        Returns:
            Time range string (e.g., "00:30 - 02:15")
        """
        if not keywords or not utterances:
            return ""
        
        # Find utterances containing keywords
        matching_utterances = []
        for utterance in utterances:
            text = utterance.get('text', '').lower()
            if any(keyword.lower() in text for keyword in keywords):
                matching_utterances.append(utterance)
        
        if not matching_utterances:
            return ""
        
        # Get time range
        timestamps = [u.get('timestamp', 0) for u in matching_utterances]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        # Convert to minutes:seconds format
        start_min = int(start_time // 60)
        start_sec = int(start_time % 60)
        end_min = int(end_time // 60)
        end_sec = int(end_time % 60)
        
        return f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

    def _parse_summary_text(self, text: str) -> str:
        """
        Parse summary text to handle markdown-like formatting and line breaks
        
        Args:
            text: Raw summary text with markdown formatting
            
        Returns:
            HTML-formatted text for PDF
        """
        if not text:
            return ""
        
        # Clean the text first
        text = self._safe_korean_text(text)
        
        # Simple approach: just add line breaks after numbered items
        import re
        
        # Add line breaks after numbered patterns (1. 2. 3. etc.)
        text = re.sub(r'(\d+\.\s*\*\*[^*]+\*\*:)', r'<br/><br/><b>\1</b>', text)
        
        # Add line breaks after sentences for better readability
        text = re.sub(r'([.!?])\s+', r'\1<br/>', text)
        
        return text
    
    def _safe_korean_text(self, text: str) -> str:
        """
        Safely encode Korean text for PDF generation with multiple fallback strategies
        
        Args:
            text: Input text that may contain Korean characters
            
        Returns:
            Safely encoded text
        """
        try:
            if not text:
                return ""
            
            # Convert to string if not already
            text = str(text)
            
            # Strategy 1: Try direct Unicode encoding
            try:
                # Normalize Unicode text
                import unicodedata
                normalized_text = unicodedata.normalize('NFC', text)
                
                # Test if current font can handle this text
                if hasattr(self, 'korean_font') and self.korean_font in ['HeiseiKakuGo-W5', 'HeiseiMin-W3', 'MalgunGothic', 'Gulim', 'Batang']:
                    return normalized_text
                    
            except Exception as e:
                print(f"Unicode normalization failed: {e}")
            
            # Strategy 2: HTML entity encoding for problematic characters
            try:
                import html
                # Convert Korean characters to HTML entities if needed
                encoded_text = text
                
                # Replace common problematic Korean characters with similar ones or romanization
                korean_replacements = {
                    # Common Korean syllables that might cause issues
                    '회의': 'Meeting',
                    '요약': 'Summary', 
                    '참가자': 'Participants',
                    '액션': 'Action',
                    '결정': 'Decision',
                    '발언': 'Speech',
                    '시간': 'Time',
                    '날짜': 'Date',
                    '생성': 'Generated',
                    '아이템': 'Items',
                    '사항': 'Items',
                    '담당': 'Assignee',
                    '마감': 'Due',
                    '외': 'etc',
                    '개': 'items',
                    '분': 'min',
                    '미정': 'TBD',
                    '알 수 없음': 'Unknown'
                }
                
                # Always replace common Korean terms with English for better compatibility
                for korean, english in korean_replacements.items():
                    encoded_text = encoded_text.replace(korean, english)
                
                # Additional replacements for common phrases
                encoded_text = encoded_text.replace('요약이 생성되지 않았습니다', 'Summary not generated')
                encoded_text = encoded_text.replace('요약이 아직 생성되지 않았습니다', 'Summary not yet generated')
                encoded_text = encoded_text.replace('생성 일시', 'Generated at')
                encoded_text = encoded_text.replace('이 문서는 Speech2SQL 시스템에서 자동 생성되었습니다', 'This document was automatically generated by Speech2SQL system')
                
                return encoded_text
                
            except Exception as e:
                print(f"HTML encoding failed: {e}")
            
            # Strategy 3: Safe fallback - remove or replace problematic characters
            safe_text = text.replace('�', '?')  # Replace replacement characters
            
            # If all else fails, try to convert Korean to romanized form
            try:
                # Simple romanization for common Korean characters
                if any('\uac00' <= char <= '\ud7af' for char in safe_text):  # Korean syllables range
                    # If Korean detected and we're using non-Korean fonts, replace with English
                    if not hasattr(self, 'korean_font') or self.korean_font in ['Helvetica', 'Times-Roman']:
                        safe_text = '[Korean Text]'
                        
            except Exception:
                pass
            
            return safe_text
            
        except Exception as e:
            print(f"Text encoding error: {e}")
            return "[Text Error]"
    
    def generate_meeting_summary_pdf(
        self,
        meeting_data: Dict[str, Any],
        utterances: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        summary_type: str = "general",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate PDF summary for a meeting
        
        Args:
            meeting_data: Meeting information
            utterances: List of utterances from the meeting
            actions: List of action items and decisions
            output_path: Optional output file path
        
        Returns:
            Path to generated PDF file
        """
        if not output_path:
            # Create temporary file
            temp_dir = os.path.join("temp", "summaries")
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"meeting_summary_{meeting_data.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        # Build PDF content
        story = []
        
        # Title with modern styling (simplified)
        title = self._safe_korean_text(meeting_data.get('title', 'Meeting Summary'))
        story.append(Paragraph(title, self.title_style))
        story.append(Spacer(1, 20))
        
        # Meeting metadata with modern table (simplified header)
        story.append(Paragraph("Meeting Information", self.heading_style))
        
        # Format meeting date properly
        meeting_date_str = 'N/A'
        if meeting_data.get('date'):
            try:
                if isinstance(meeting_data['date'], str):
                    # Parse ISO format date (datetime already imported at top)
                    parsed_date = datetime.fromisoformat(meeting_data['date'].replace('Z', '+00:00'))
                    meeting_date_str = parsed_date.strftime('%Y-%m-%d')  
                else:
                    meeting_date_str = str(meeting_data['date'])
            except Exception as e:
                print(f"Date parsing error: {e}")
                meeting_date_str = str(meeting_data.get('date', 'N/A'))
        
        # Format duration properly
        duration_seconds = meeting_data.get('duration', 0)
        if duration_seconds > 0:
            duration_minutes = int(duration_seconds / 60)
            duration_str = f"{duration_minutes} min"
        else:
            duration_str = "N/A"
        
        meta_data = [
            ['Date', meeting_date_str],
            ['Duration', duration_str],
            ['Participants', self._safe_korean_text(', '.join(meeting_data.get('participants', [])) or 'TBD')],
            ['Generated at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.colors['bg_light']),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.colors['text_dark']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), getattr(self, 'korean_font', 'Helvetica')),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['border']),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [self.colors['bg_light'], colors.white])
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 25))
        
        # Summary with proper formatting (simplified header)
        raw_summary = meeting_data.get('summary', 'Summary not generated.')
        formatted_summary = self._parse_summary_text(raw_summary)
        story.append(Paragraph("Meeting Summary", self.heading_style))
        story.append(Paragraph(formatted_summary, self.body_style))
        story.append(Spacer(1, 20))
        

        
        # Content based on summary type
        if summary_type == "general":
            # Add time information for numbered summary points
            if utterances and len(utterances) > 0:
                # Extract numbered points from summary and add time info
                summary_with_time = self._add_time_info_to_summary(raw_summary, utterances)
                if summary_with_time != raw_summary:
                    story.append(Paragraph("Summary with Time Information", self.heading_style))
                    formatted_summary_with_time = self._parse_summary_text(summary_with_time)
                    story.append(Paragraph(formatted_summary_with_time, self.body_style))
                    story.append(Spacer(1, 20))
        
        elif summary_type == "meeting":
            # Action items and decisions (for meeting summary type)
            action_items = [a for a in actions if a.get('action_type') == 'assignment']
            if action_items:
                story.append(Paragraph("Action Items", self.heading_style))
                
                for i, action in enumerate(action_items, 1):
                    description = self._safe_korean_text(action.get('description', ''))
                    action_text = f"<b>{i}.</b> {description}"
                    if action.get('assignee'):
                        assignee = self._safe_korean_text(action['assignee'])
                        action_text += f" <i>(Assignee: {assignee})</i>"
                    if action.get('due_date'):
                        action_text += f" <i>(Due: {action['due_date']})</i>"
                    
                    story.append(Paragraph(action_text, self.list_style))
                
                story.append(Spacer(1, 20))
            
            # Decisions
            decisions = [a for a in actions if a.get('action_type') == 'decision']
            if decisions:
                story.append(Paragraph("🎯 Decisions", self.heading_style))
                
                for i, decision in enumerate(decisions, 1):
                    description = self._safe_korean_text(decision.get('description', ''))
                    decision_text = f"<b>{i}.</b> {description}"
                    story.append(Paragraph(decision_text, self.list_style))
                
                story.append(Spacer(1, 20))
        
        # Footer with modern styling
        story.append(Spacer(1, 40))
        footer_text = f"<i>Generated by Speech2SQL • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        story.append(Paragraph(footer_text, self.meta_style))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def generate_analytics_pdf(
        self,
        analytics_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate PDF report for analytics data
        
        Args:
            analytics_data: Analytics information
            output_path: Optional output file path
        
        Returns:
            Path to generated PDF file
        """
        if not output_path:
            temp_dir = os.path.join("temp", "analytics")
            os.makedirs(temp_dir, exist_ok=True)
            output_path = os.path.join(temp_dir, f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        story = []
        
        # Title (simplified)
        story.append(Paragraph("Analytics Report", self.title_style))
        story.append(Spacer(1, 20))
        
        # Analytics summary (simplified header)
        story.append(Paragraph("Key Metrics", self.heading_style))
        
        stats_data = [
            ['Total Meetings', str(analytics_data.get('total_meetings', 0))],
            ['Total Summaries', str(analytics_data.get('total_summaries', 0))],
            ['Total Action Items', str(analytics_data.get('total_actions', 0))],
            ['Average Duration', f"{analytics_data.get('average_duration_minutes', 0):.1f} min"],
            ['Summary Completion Rate', f"{analytics_data.get('summary_completion_rate', 0):.1f}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), getattr(self, 'korean_font', 'Helvetica')),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd'))
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Monthly trend
        monthly_data = analytics_data.get('monthly_meetings', [])
        if monthly_data:
            story.append(Paragraph("Monthly Meeting Trends", self.heading_style))
            
            month_table_data = [['Month', 'Meetings']]
            for month_info in monthly_data[-6:]:  # Last 6 months
                month_table_data.append([
                    month_info.get('month', ''),
                    str(month_info.get('count', 0))
                ])
            
            month_table = Table(month_table_data, colWidths=[2*inch, 2*inch])
            month_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), getattr(self, 'korean_font', 'Helvetica')),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd'))
            ]))
            
            story.append(month_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Speech2SQL Analytics"
        story.append(Paragraph(footer_text, self.meta_style))
        
        doc.build(story)
        return output_path


# Convenience functions
def generate_meeting_pdf(meeting_data: Dict[str, Any], utterances: List[Dict[str, Any]], 
                        actions: List[Dict[str, Any]], summary_type: str = "general", output_path: Optional[str] = None) -> str:
    """Generate meeting summary PDF"""
    generator = PDFGenerator()
    return generator.generate_meeting_summary_pdf(meeting_data, utterances, actions, summary_type, output_path)


def generate_analytics_pdf(analytics_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Generate analytics report PDF"""
    generator = PDFGenerator()
    return generator.generate_analytics_pdf(analytics_data, output_path)
=======
# 생성된 요약 내용을 pdf로 생성
>>>>>>> f4019648f6d7bc1c24203184b859f5e6aca469a8
