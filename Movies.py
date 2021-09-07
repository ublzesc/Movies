import re
from requests import get
from bs4 import BeautifulSoup as BS
import os
import pandas as pd

#Diccionario para reemplazar adiciones inecesarias en los nombres de los archivos
dic = [r".* - ",r"\.[^.]*$",r" \(Disc 1\)",r" \(Disc 2\)",r" \(Director's Cut\)",r" \(Final Cut\)",r" \(Final Alternativo\)",r" \(Ultimate Cut\)",
       r" \(Extended Collectors Edition\)",r" \(Unrated Edition\)",r" \[Extended\]",r"\.SPA",r"\.ENG"]

#Función para obtener por web scraping de IMDb la información de una película.
#Parámetros
#name_year: string con formato "[Nombre] ([aaaa])" a encontrar.
#num: el número de resultado que se quiere considerar de la búsqueda en IMDb.
def IMDb(name_year,num=0,getnrate=False,new=True):
    print(name_year)
    imdbtitle,origtitle,country,director,genre,duration,year,rate,metarate,nrate = "","","","","","","","","",""
    name = re.sub(" \\([^\\)]+\\)", "", name_year)
    year = name_year[name_year.find("(") + 1:name_year.find(")")]
    if name_year.find("(") == -1:
        URL = "https://www.imdb.com/find?q=" + re.sub(" ", "+", name)
        html_soup = BS(get(URL).content, "html.parser")
        aux = html_soup.find_all("td", class_="result_text")
        aux = [x for x in aux if re.match(r'/title', x.a["href"])]
    else:
        URL = "https://www.imdb.com/search/title/?title=" + re.sub(" ", "+", name) + "&release_date=" + year + "-01-01," + year + "-12-31"
        html_soup = BS(get(URL).content, "html.parser")
        aux = html_soup.find_all("h3", class_="lister-item-header")
    if aux != []:
        if new:
            aux = aux[num].a["href"]
            URL = "https://www.imdb.com" + aux
            html_soup = BS(get(URL).content,"html.parser")
            aux = html_soup.find("h1", {"data-testid":"hero-title-block__title"}).text
            imdbtitle = re.sub("\xa0\\([^\\)]+\\)", "", aux)
            aux = html_soup.find_all("div", {"data-testid":"hero-title-block__original-title"})
            if aux != []:
                origtitle = re.sub("Original title: ", "", aux[0].text)
            else:
                origtitle = imdbtitle
            aux = html_soup.find("ul", {"data-testid":"hero-title-block__metadata"}).find_all("li")
            if len(aux) > 0:
                if aux[0].text == 'TV Movie' or aux[0].text == 'TV Special':
                    year = aux[1].a.text
                else:
                    year = aux[0].a.text
            if len(aux) > 1:
                duration = aux[len(aux) - 1].text
            URLaux = URL + "fullcredits"
            html_soupaux = BS(get(URLaux).content,"html.parser")
            aux = html_soupaux.find(lambda tag: tag.name=='table').find('a').text
            director = aux[1:len(aux)-1]
            genre,country = [],[]
            for gen in html_soup.find("div", {"data-testid":"genres"}).find_all("span"):
                genre.append(gen.text)
            genre = "/".join(genre)
            for cou in html_soup.find("li", {"data-testid":"title-details-origin"}).find_all("a"):
                country.append(cou.text)
            country = "/".join(country)
            aux = html_soup.find_all("div", {"data-testid":"hero-rating-bar__aggregate-rating__score"})
            if aux != []:
                rate = aux[0].span.text
                URLaux = URL + "ratings"
                html_soupaux = BS(get(URLaux).content,"html.parser")
                nrate = html_soupaux.find("div", class_="allText").text.split('\n')[2].lstrip()
            aux = html_soup.find_all("span",class_="score-meta")
            if aux!=[]:
                metarate=aux[0].text
        else:
            aux=aux[num].a["href"]
            URL="https://www.imdb.com"+aux
            html_soup=BS(get(URL).text,"html.parser")
            aux=html_soup.find_all("div",class_="title_wrapper")[0].h1.text
            aux=re.sub("\xa0\\([^\\)]+\\)","",aux)
            imdbtitle=aux[:-1]
            aux=html_soup.find_all("div",class_="originalTitle")
            if aux!=[]:
                origtitle=re.sub(" \\(original title\\)","",aux[0].text)
            else:
                origtitle=imdbtitle
            aux=html_soup.find_all("div",class_="title_wrapper")[0].h1.find_all("span")
            if aux!=[]:
                year=aux[0].a.text
            aux=html_soup.find_all("div",class_="subtext")[0].find_all("time")
            if aux!=[]:
                duration=re.sub("\n","",aux[0].text).strip()
            director=html_soup.find_all("div",class_="credit_summary_item")[0].a.text
            genre,country=[],[]
            for gen in html_soup.find_all("div",class_="subtext")[0].find_all("a",href=re.compile("genre")):
                genre.append(gen.text)
            genre="/".join(genre)
            for cou in html_soup.find_all("a",href=re.compile("country_of_origin")):
                country.append(cou.text)
            country="/".join(country)
            aux=html_soup.find_all("div",class_="ratingValue")
            if aux!=[]:
                rate=aux[0].span.text
            aux=html_soup.find_all("div",class_="titleReviewBarItem")
            if aux!=[]:
                aux=aux[0].find_all("a",href=re.compile("criticreviews"))
                if aux!=[]:
                    metarate=aux[0].span.text
            aux=html_soup.find_all("span",itemprop="ratingCount")
            if aux!=[]:
                nrate=aux[0].text
    if getnrate:
        ret=[imdbtitle,origtitle,country,director,genre,duration,year,rate,nrate,metarate]
    else:
        ret=[imdbtitle,origtitle,country,director,genre,duration,year,rate,metarate]
    return ret

#Función para obtener un dataframe con nombre, ruta e indicador de vista, de todas las películas en un directorio y todos sus subdirectorios.
#Parámetros
#ruta: string con la ruta del directorio a inspeccionar.
#vitas: indica si una película ha sido vista.
def Movies_list(ruta,vista=0):
    aux_r=[dp for dp, dn, filenames in os.walk(ruta) for f in filenames]
    aux_m=[f for dp, dn, filenames in os.walk(ruta) for f in filenames]
    aux_r=[aux_r[x] for x in range(len(aux_m)) if re.search("\\([0-9][0-9][0-9][0-9]\\)",aux_m[x])]
    aux_m=[aux_m[x] for x in range(len(aux_m)) if re.search("\\([0-9][0-9][0-9][0-9]\\)",aux_m[x])]
    aux_m=[os.path.splitext(x)[0] for x in aux_m]
    for txt in dic:
        aux_m=[re.sub(txt,"",x) for x in aux_m]
    aux=pd.DataFrame({'Name_Year':aux_m,'Ruta':aux_r}).drop_duplicates(subset=['Name_Year']).sort_values('Name_Year')
    aux["Vista"]=vista
    return aux.reset_index(drop=True)

#Función para crear una base con la información de IMDb de todas las películas de una lista.
#Parámetros
#movie_list: dataframe con nombre, ruta e indicador de vista, de varias películas.
def DF_nuevo(movie_list):
    cols=["imdbtitle","origtitle","country","director","genre","duration","year","rate","metarate"]
    movie_list[cols]=pd.DataFrame([["","","","","","","","",""]],index=movie_list.index)
    movie_list.reset_index(drop=True,inplace=True)
    for i in range(len(movie_list.Name_Year)):
        aux=IMDb(movie_list.iloc[i,0])
        for j in range(len(cols)):
            movie_list.loc[movie_list.index.values==i,cols[j]]=aux[j]
    return movie_list

#Función para crear una base con la información de IMDb de todas las películas de una lista.
#Parámetros
#movies: list with movie names
def newDF(movies):
    cols = ["title","origtitle","country","director","genre","duration","year","imdbrate","nrate","metarate"]
    moviesDF = pd.DataFrame(columns = cols)
    for i in range(len(movies)):
        moviesDF.loc[i] = IMDb(movies[i], getnrate=True)
    moviesDF.loc[:,'title'] = movies
    moviesDF = moviesDF.sort_values("imdbrate", ascending=False)
    return moviesDF.reset_index(drop=True)