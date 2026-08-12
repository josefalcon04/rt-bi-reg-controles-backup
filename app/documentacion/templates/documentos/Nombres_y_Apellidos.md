# Nombres y Apellidos



Este proceso se encarga de generar el detalle de nombres y apellidos, como punto de partida el usuario envia la información input.



---

Nombres y apellidos



## 1. Etapa de matricula: 

python Frame_Load_Excel_to_TDT.py LoadNZ_NOMAPE.xlsx --Matricula

python Frame_LoadSP.py SPTdt_F_NOMAPE.xlsx  --Matricula

python Frame_Load_Extract.py EXNZ_NOMAPE.xlsx



Nota: hay que cambiar el formato de la fecha en YYYY-MM-DD

ejecutar

/datos5/FG_REG_DESA/InputFiles



##  2. Etapa de ejecución:



1.- python Frame_NZLoad.py LNOMAPEL

2.- python Frame_EjecutaSP.py SPNOMAPE

3.- python Frame_Extractor_NZ.py EXNOMAPE

##  3. Resultado en Netezza:

SELECT * FROM DESARROLLO_AM..TMP_NOMBAPE_X01;



