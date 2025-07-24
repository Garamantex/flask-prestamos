# app.py
from app import create_app

app = create_app()
app.debug = True

@app.template_filter('moneda_cl')
def moneda_cl(value):
    try:
        value = int(value)
        return "${:,.0f}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return value

if __name__ == '__main__':
    app.run(debug=True)
