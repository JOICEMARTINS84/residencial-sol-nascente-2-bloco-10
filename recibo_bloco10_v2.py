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
        mascara=Image.open(BytesIO(b64decode('iVBORw0KGgoAAAANSUhEUgAAATAAAACCAQAAAADp9amUAAAEhklEQVR42qWYPY7jNhiGH5LG0MXAcunCGfsCAbacwlk7J8nmBi6nGKwJJEDK5Ag+RpJmCWyRdJkTJJzsAJlSs9gE2kAjpqAkS7YpCRs1tuyX3w+/v5eET3uUOferHLb4BDYati4ZJm0gbKBtV8Ngq/+j9ORJB0kTw2ByoKeuF5YUMLJ9sCQVOeNI3hy+ZiDFrz/1xdx779OrPhe2z0IsJ8seYdobED7vgS0ygHXWA/MGQPfAVNAm8m4XLh9ONugc7MU+vDrTpbNSpr/rDNbFh/A5zjs3LimFJJF8K591XTC3XbBqH152lowqTaPgzw7Y5V1dfk9dAT3Ule5oXF81ftnEpVUBFw5lo9LUY/XmKJZR2Mj19UAJMKvtsfhp1LSXzR64jUr7uXqbwvlKlYCoM9sDUU/lXbNVjmKwqm+oSNyPQqW5AeYx2Kr2M43BZBMm0q5uXOX1SrhYx5eNdptLF2vWEuS+SqFWq1RH+6zr5do0lOofI+PHJQCTyqHrttKiyskw/aoM+fwINq9zsogOLwnVqpFtJW5mzg+MEKvaVOdao11Ur+OPzVYp7n1LqbR1splQ+OEP27ZtVNkwaXWjURt34AArYRseat2WVpuQt3JDH2KlUmS961VIyx42rZcv8sQdto00qL8Jb/Nq1xfe+0zW/eNoys/LvVYO9hey7kBlSKtlm9KVW57E18tDEJSdN4Vu03J8ZsCk4V0Z0hJm0kAk/Bh4Lzl0o1XQHZ4nFwJc9mJhWuVXtUHxztKYrwelh0hbgAcLTPiWI2lXIVW0WWeA+A3AZyfUYbX2GZAERep3IPHmBLbz3ltIEp8zC2N4l50QkcR77zO42rmcW1QGyttjmPL+eyMK+MKrnBydwqIx0UUV4DSBBewynatsrB34RjUET4W/d1egDN4mWZKttCVp1KP0G4Cr56UDCiPYTM0028ws2/fNjHkF4K2yq5JovE7X9/nOKH8y5HSOMjcAOiV3z389e9N0oAzW7KEqsPGd+Fv9k8nsS/dwMks86BD5hdHvfnnn12+9b47GsGkZTEJIX5K8/eObfKFCOFuwha1htyyUVxkiRKCldAfMQ6JlvNa5so2CazOflTKBHefnyJkELh6AfAQgU/WBx/Ow2R7YjA0wcqM033dM3e0EIDEL28kbtleBK62jfNEBuDnAa4oolbUAbgVQqCzGHGYbQLgVoIrLKOyzg4UjXtx1eqBMCize+BhdEY+H9rZ49Rx11AJoYYF8kcakXdoDIckff4hJC8NHKwPaxalUCRsB432chYTOPdENWhvnDfNJg9aeUVoNqmn8FADIklTkBVw8xmElqVguy/SM5Uf4uL4OlRN7ysn24qbLtHq0b1N0xxlAFvW+zO46YOU8fIJXHTS7qu5722mavK5iWx1nOg9QznaZVtFXMTJeDJA2Vs9DLhPeVKe7bth0u6ffNil2coi05ftBFx2bu+7za9heVQy6Npn/23NmDqH3rkeajN/jNGFPBkgf+6RlG0jouxyQ+TUi/YjtU+u990b33uGsvc/oh2lffPo90dHzH76TfEygyRXgAAAAAElFTkSuQmCC'))).convert('L')
        x=1575-mascara.width//2
        y=600-mascara.height
        im.paste((8,29,77),(x,y,x+mascara.width,y+mascara.height),mascara)
    d.line((1160,605,1990,605),fill=azul,width=3)
    t(1575,621,'Daniela — Síndica',34,False,cinza,'mt')
    return im

def exportar(im,tipo):
    b=BytesIO()
    if tipo=='JPG':im.save(b,'JPEG',quality=96,subsampling=0,dpi=(300,300))
    else:im.save(b,'PDF',resolution=300)
    return b.getvalue()
