FROM node:22-bookworm-slim AS node
FROM python:3.11-slim-bookworm
COPY --from=node /usr/local/bin/node /usr/local/bin/node
ENV PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 NODE_ENV=production
WORKDIR /service
COPY api/requirements.txt /service/api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt
COPY api /service/api
COPY app/lib/corrosion.ts /service/app/lib/corrosion.ts
COPY pinn_model.py graph_dataset.py pdf_table2_galvanic_series.csv /service/
COPY ["Post training", "/service/Post training"]
RUN python -c "from pathlib import Path; files=list(Path('Post training').rglob('*.pt')); assert len(files)>=3 and all(p.stat().st_size>1000 for p in files), 'Git LFS checkpoint content is missing'"
RUN useradd --create-home --uid 10001 mast
USER mast
EXPOSE 8000
CMD ["node", "--experimental-strip-types", "api/server.mjs"]
