#FROM default-route-openshift-image-registry.apps.ocptest.gp.inet/nirvana-qa/python311-bi-opd:1.0.0
FROM telefonicaavillacortal/python311-bi-reg:1.1.0

RUN mkdir -p /app

WORKDIR /app

COPY . .

# Directorios con escritura requerida por la aplicación
RUN mkdir -p /app/static/img \
    /app/static/dashboards \
    /app/data \
    /app/app/documentacion/templates/documentos \
    && chmod -R 777 /app/static/img \
    && chmod -R 777 /app/static/dashboards \
    && chmod -R 777 /app/data \
    && chmod -R 777 /app/app/documentacion/templates/documentos

#RUN pip install --no-cache-dir -r requirements.txt

# Cache de Matplotlib
ENV MPLCONFIGDIR=/tmp/matplotlib

ENV PYTHONUNBUFFERED=1

EXPOSE 8082

ENTRYPOINT ["python"]
CMD ["run.py"]