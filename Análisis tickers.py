import streamlit as st
from core.style import inject_css

st.set_page_config(page_title="Plataforma Financiera", page_icon="📊", layout="wide")
inject_css()

# Para agregar una sección nueva: creá un archivo en views/ y sumá una línea acá.
pages = [
    st.Page("views/analisis.py", title="Análisis",  default=True),
    st.Page("views/portfolio.py", title="Portfolio"),
    # st.Page("views/simulador.py", title="Simulador"),
]

pg = st.navigation(pages, position="top")
pg.run()
