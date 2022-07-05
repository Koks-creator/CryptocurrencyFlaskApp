from bokeh.plotting import figure,output_file,show, ColumnDataSource
from bokeh.models.tools import HoverTool
from bokeh.transform import factor_cmap
from bokeh.palettes import Dark2, Spectral6,viridis
from bokeh.embed import components
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
from time import sleep
from bokeh.embed import components
from bokeh.resources import CDN


url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
api_request = requests.get(url)
api = json.loads(api_request.content)
names_list = []
full_names_list = []
lista_kursow = []
lista_linkow = []
lista_kapitalizacji = []
lista_wolumenow = []
lista_obiegow = []
lista_zmian = []

for i in range(20):
    names_list.append(api[i]['symbol'].upper())
    full_names_list.append(api[i]['name'])
    lista_kursow.append(api[i]['current_price'])
    lista_linkow.append(api[i]['image'])
    lista_kapitalizacji.append(api[i]['market_cap'])
    lista_wolumenow.append(api[i]['total_volume'])
    lista_obiegow.append(api[i]['circulating_supply'])
    lista_zmian.append(api[i]['price_change_percentage_24h'])

print(lista_kursow)
print(names_list)
print(full_names_list)

#Bohehowe rzeczy
source = {
    "Name": names_list,
    "Pelne_nazwy":full_names_list,
    "Price": lista_kursow,
    "Image": lista_linkow,
    "kapitalizacja": lista_kapitalizacji,
    "wolumen": lista_wolumenow,
    "obieg": lista_obiegow,
    "zmiana":lista_zmian
}
p = figure(
    x_range=names_list,
    plot_width=800,
    plot_height=600,
    title="xd",
    y_axis_label="Price",
    tools="pan,box_select,zoom_in,zoom_out,save,reset"
)

p.vbar(
    x="Name",
    top="Price",
    bottom=0,
    width=0.4,
    source=source,
    legend_field='Name'



)

# Add Legend
p.legend.orientation = 'vertical'
p.legend.location = 'top_right'
p.legend.label_text_font_size = '10px'

# Add Tooltips


# Show results
show(p)
    #sleep(10)