# Financial-reports
Este es el ciclo completo para cada cambio.

Ciclo para cada feature

1. Sincronizá main (en la terminal de Git, parado en Financial-reports)

bash
git checkout main
git pull

2. Creá una rama para el cambio

bash
git checkout -b nombre-del-cambio

3. Editá los archivos y probá en local

En la otra terminal, con la app corriendo:

bash
conda activate plataforma
streamlit run "Análisis tickers.py"

Si rompiste algo, git restore nombre_del_archivo lo devuelve a como estaba en el último commit.

4. Revisá qué cambiaste

bash
git status
git diff

5. Commit y push

bash
git add .
git commit -m "descripción corta del cambio"
git push -u origin nombre-del-cambio

El -u solo hace falta en el primer push de cada rama nueva. Si volvés a pushear a la misma rama, alcanza con git push.

6. Publicá desde GitHub (web)

“Compare & pull request”, después “Create pull request” y “Merge pull request”. Streamlit Cloud redeploya solo en uno o dos minutos.

7. Volvé a sincronizar tu compu

bash
git checkout main
git pull

Opcional, para limpiar: git branch -d nombre-del-cambio.