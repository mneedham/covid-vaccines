import streamlit as st

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))


# https://stackoverflow.com/questions/55169344/how-to-make-altair-plots-responsive
def make_charts_responsive():
    st.write("""
    <style>
    canvas.marks {
        max-width: 100%!important;
        height: auto!important;
    }
    </style
    """, unsafe_allow_html=True)    