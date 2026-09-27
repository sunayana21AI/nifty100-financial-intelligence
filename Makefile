load:
	python src/etl/loader.py

test:
	pytest tests/

clean:
	rm -rf __pycache__

report:
	echo "Generate report"

dashboard:
	streamlit run src/app.py

api:
	uvicorn src.api:app --reload