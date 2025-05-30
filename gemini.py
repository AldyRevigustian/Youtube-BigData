from google import genai
import config

class GeminiSummarizer:
    def __init__(self):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
    
    def generate_summary(self, comments_text):
        """Generate summary from comments text"""
        try:
            prompt = f"""
            Berikut adalah komentar-komentar dari live streaming YouTube:

            {comments_text}

            Buatkan ringkasan yang mencakup:
            1. Tema utama yang dibicarakan
            2. Sentimen umum penonton
            3. Pertanyaan atau permintaan utama
            4. Highlight menarik dari komentar

            Buat ringkasan dalam bahasa Indonesia, maksimal 200 kata.
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash", contents=prompt
            )
            
            return response.text
        except Exception as e:
            return f"Error generating summary: {str(e)}"

if __name__ == "__main__":
    # Test the summarizer
    summarizer = GeminiSummarizer()
    test_comments = "User1: Bagus sekali streamnya!\nUser2: Kapan episode selanjutnya?\nUser3: Terima kasih untuk kontennya"
    summary = summarizer.generate_summary(test_comments)
    print(summary)