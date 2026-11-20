from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from base64 import b64decode
BASE=Path(__file__).parent
MESES=['janeiro','fevereiro','mar\u00e7o','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']

def fonte(tamanho, bold=False):
    nomes=['arialbd.ttf' if bold else 'arial.ttf', 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf']
    for nome in nomes:
        for p in [nome, str(Path('C:/Windows/Fonts')/nome), '/usr/share/fonts/truetype/dejavu/'+nome]:
            try: return ImageFont.truetype(p,tamanho)
            except OSError: pass
    return ImageFont.load_default(size=tamanho)

def dinheiro(c):
    return 'R$ '+f'{c/100:,.2f}'.replace(',','_').replace('.',',').replace('_','.')

def imagem(reg, rubrica=False):
    from num2words import num2words
    n,apt,c,mes,ano,data,forma,nome=reg
    im=Image.new('RGB',(2143,734),'white')
    d=ImageDraw.Draw(im); azul='#203b50'; cinza='#24323d'; verde='#20734b'
    def t(x,y,s,z=39,b=False,cor=cinza,anchor=None):
        d.text((x,y),s,font=fonte(z,b),fill=cor,anchor=anchor)
    def ajusta(x,y,s,larg,z=40,b=True):
        while z>17 and d.textlength(s,font=fonte(z,b))>larg:z-=1
        t(x,y,s,z,b)
    def linha(x,y,f):d.line((x,y,f,y),fill='#89969e',width=2)
    d.rectangle((22,22,2121,712),outline=azul,width=3)
    t(78,45,f'RECIBO N\u00ba {n:04d}',60,True,azul)
    t(78,126,'Residencial Sol Nascente 2 — Bloco 10',37)
    d.rectangle((1574,55,2064,181),outline=azul,width=3)
    t(1819,79,'VALOR RECEBIDO',29,True,azul,'mt')
    s=dinheiro(c); z=54
    while d.textlength(s,font=fonte(z,True))>460:z-=1
    t(1819,118,s,z,True,azul,'mt')
    d.line((78,202,2064,202),fill=azul,width=2)
    t(78,225,'Recebemos de',34)
    tamanho = 39
    while tamanho > 19 and d.textlength(nome,font=fonte(tamanho,True)) > 1370:
        tamanho -= 1
    if d.textlength(nome,font=fonte(tamanho,True)) <= 1370:
        t(347,224,nome,tamanho,True)
    else:
        corte = len(nome)
        while d.textlength(nome[:corte],font=fonte(tamanho,True)) > 1370:
            corte -= 1
        t(347,217,nome[:corte],tamanho,True)
        t(347,242,nome[corte:],tamanho,True)
    t(1770,225,f'Apto. {apt}',35,True)
    reais,cent=divmod(c,100)
    s=(num2words(reais,lang='pt_BR')+(' real' if reais==1 else ' reais')) if reais else ''
    if cent:s+=(' e ' if s else '')+num2words(cent,lang='pt_BR')+(' centavo' if cent==1 else ' centavos')
    ajusta(78,278,'A importância de '+s+'.',1980,35,False)
    t(78,335,'Referente \u00e0 taxa condominial de',37);t(700,335,f'{MESES[mes-1]}/{ano}',40,True);linha(690,385,2064)
    t(78,400,'Data do pagamento:',37);t(472,397,'/'.join(data.split('-')[::-1]),40,True);linha(462,449,935)
    t(1025,400,'Forma de pagamento:',37)
    for x,label in [(1454,'Dinheiro'),(1780,'Pix')]:
        d.rectangle((x,406,x+35,441),outline=azul,width=3)
        if forma==label:d.line([(x+7,423),(x+15,434),(x+31,413)],fill=verde,width=5,joint='curve')
        t(x+51,400,label,37)
    t(78,532,'PAGO',58,True,verde)
    if rubrica:
        # Modelo de rubrica: aplicar apenas com autorização da síndica.
        mascara=Image.open(BytesIO(b64decode('iVBORw0KGgoAAAANSUhEUgAAAVMAAACRAQAAAABWZ2bSAAAFF0lEQVR42qVYu3LjNhQ9ADmGCs1SpQuHUr4gKl0wlpL8iD/BRQoVHgvrSZEyf2B/RorMGtlkJi73E5DdLVRSMy5oD8WbAuBTJAFN2NiyDq8PLu49OBfA/3oCOfAFP/5TCH/s5AQO0QlxT8EuTsBenYDNT1hb5h+XnYBF6o/l8MeG+gQOyh/rWQ5zyoG5F1QQkR7ethaHDYCLsSZohP0DAGfffPSgsCWJgNLMp81IA5jnPtioMG+kHmu7+QwAB5n6ULDhPeJOX231TtzY5bPd4jM3Byr3eeumW6YqnksXh+mu7Ph07cIuH8uOf1kOYUuheypfyouJL11kw/rAO3RZBtfaZiVdnsJVk3cVGeVqIlZxFArR+BnAX6ouVsjW47WrGkIdqNG4s+rr2ZhYt5eGK4BpT8lNRoSSt3cNiVNwVOs/bMbiTpRb1Evsd7Il6uEYtpK7BR8V4FYatFAj6+MAgqogTUw+gq1OCG5EXY9g6zTomXTkoQKEilxbkdRFlgBAXOvhUdzGutuly349wm7quHnrkD2WtroGEwN7V737ezcur3PEOu0iu9hQdeJWTzzihVLTahVkc5SHqGbQqbDN0V7EjYJslRhLj+JW6eV60loM//co7qbW11lbb5XuYFm99m453Hfj1umdSEO9KD+HqsuhoTnrlkmM0N2LUNbHVlvS48ZpIAqAQzS2aTO0S6uMZe3eYu16TqrMzxUgwOuqOiqHrKQkNABI4LJbDtUbaUmJqAAixYddPSuxcxAHXsDruMyWQ7U59hemcW+zfl0fQVGrT4K/DKVVaWt4M98zW0ItSoGiWflZY0Adwue9yc7HY1tq1QFCGjEUD8YHVZvJm+24tkZ1bpr9wYT9pc5MxTcWRCa+/XkLgFHW5z2/zcy8EAkb4hbAOzz3YIWy89ji8iDl2dpI+M2hIVsVByLSjDRwS4oQKcw1IEj1+LMIh1DTZAYE9AOwNJp9SeseK09FKhSwASgNCCT1XIKR7rH9Eb3XQgIXYCSjglGgV0DUaVZTD9uUaVMOQYH5B0FCF8C2czQurUsNlDEvIsMqiYr5lwIBqXbJfgKAi9dKHSY7rN6+fLieAkl7Zba89XuEiD8bS8XucvHnPTRTewDRvmPlckDY0lkhSPf59pXmRLIl2Ca/F1+BicV+j3DPc+wOKQ6yx+9cPwJk1eEW5zrf4eHnDF/73GQOIDb9G6RYMVJ3QFD0HUZRCuDC9JnQKAJqKEGHw/I3AAvTZxPNClCjEjs5e+IAkn+sVeMvxduwf3izvQkACzlNsRv2D7vGYLHCTNOw8zPOP43s1L11O0QdG1vHCqc1YgYrsmBs7rZfGuwkm45hw0/ml7Wp5uWnkfni3BS0ygFgzRQboXtlVSwFwHIavX64NVikAIKUxtynVW/BNIBIb/WIP+MWyzWA2aMa3rOwfYdwLX2ufmIhXfcqvMQWVYO4HWISAYj0eFyLzak5bg089vC6jAE4Ztjy5LtJmuNWP4eGQ8TZyzi28jQJcO6Y+0tbojfASvrdwum0NlBDHKK6hII3B7ao0zHdObCLykzWc/pQndUpZU/cgS3D/v165qALXomnPN+5sPX11vWja2ix1jmIgwKecUNMXXRr+xb/9OyNZZL5chA/HuCLRe9h1nlsfiOCd9zZwQNrF3ftQcFOOIKUR9x9k7UDm0kAgdIecY1vXxVet50sAwSlfjejpBhRz7jY96yIKPXERkTF+D1qgzD55PbU5z/BbrDMTag0ZwAAAABJRU5ErkJggg=='))).convert('L')
        x=1575-mascara.width//2
        y=600-mascara.height
        im.paste('#081d4d',(x,y,x+mascara.width,y+mascara.height),mascara)
    d.line((1160,605,1990,605),fill=azul,width=3)
    t(1575,621,'Daniela — Síndica',34,False,cinza,'mt')
    return im

def exportar(im,tipo):
    b=BytesIO()
    if tipo=='JPG':im.save(b,'JPEG',quality=96,subsampling=0,dpi=(300,300))
    else:im.save(b,'PDF',resolution=300)
    return b.getvalue()
