
[아파트 가치 평가 프로그램 실행 방법]

1. Python 설치 필요 (3.8~3.11 권장)
2. 압축 해제 후 폴더 이동
3. 가상환경 생성 (선택):
   python -m venv venv
   source venv/bin/activate (Windows: venv\Scripts\activate)
4. 의존성 설치:
   pip install -r requirements.txt
5. .env 파일에서 OPENAI_API_KEY 입력
6. 실행:
   streamlit run app.py
