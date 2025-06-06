#FROM default-route-openshift-image-registry.apps.ocptest.gp.inet/nirvana-qa/python311-bi-opd:1.0.0
FROM telefonicaavillacortal/python311-bi-reg


RUN mkdir /app
WORKDIR /app
 
COPY . .
 
#RUN pip install --no-cache-dir -r requirements.txt

 # Establecer variable de entorno
ENV PYTHONUNBUFFERED 1

EXPOSE 8082
 
# Comando de inicio
ENTRYPOINT ["python"]
CMD ["run.py"]
