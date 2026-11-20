import sqlite3
import os
from banco_bloco10 import preparar, conectar_postgres
from psycopg.conninfo import make_conninfo
import base64
import json
from urllib.parse import quote
import streamlit.components.v1 as components
from pathlib import Path
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import streamlit as st
from recibo_bloco10 import imagem, exportar, dinheiro, MESES
BASE=Path(__file__).parent
DB=BASE/'pagamentos.sqlite3'
st.set_page_config(page_title='Gestão Condominial | Bloco 10',page_icon='🏢',layout='wide')

# Não usar SQLite silenciosamente se a conexão configurada estiver indisponível.
def segredo(nome):
    try:
        return str(st.secrets.get(nome, os.environ.get(nome,'')))
    except FileNotFoundError:
        return os.environ.get(nome,'')
st.header('Residencial Sol Nascente 2 — Bloco 10')
st.caption('Síndica Daniela')
senha = segredo('APP_ACCESS_PASSWORD')
if not senha:
    st.info('Configure APP_ACCESS_PASSWORD nos Segredos para habilitar a administração.')
    st.stop()
import hmac
import hashlib
assinatura = hashlib.sha256(senha.encode()).digest()
if st.session_state.get('acesso') != assinatura:
    with st.form('acesso', clear_on_submit=True):
        entrada = st.text_input('Senha da administração', type='password')
        entrar = st.form_submit_button('Entrar')
    if entrar:
        if hmac.compare_digest(entrada.encode(), senha.encode()):
            st.session_state['acesso'] = assinatura
            st.rerun()
        st.error('Senha incorreta.')
    st.stop()
if st.sidebar.button('Sair'):
    st.session_state.clear()
    st.rerun()

DATABASE_URL=segredo('DATABASE_URL').strip()
campos_db={k:segredo('DB_'+k.upper()) for k in ('host','port','dbname','user','password')}
if any(campos_db.values()):
    if not all(campos_db.values()):
        st.error('Preencha todos os campos DB_HOST, DB_PORT, DB_DBNAME, DB_USER e DB_PASSWORD nos Secrets.')
        st.stop()
    try:
        DATABASE_URL=make_conninfo(**campos_db,sslmode='require')
    except Exception:
        st.error('Configuração do banco inválida. Confira os campos separados nos Secrets.')
        st.stop()

if not DATABASE_URL:
    st.info('Configure a conexão PostgreSQL nos Secrets do aplicativo do Bloco 10 para iniciar.')
    st.stop()

if DATABASE_URL:
    @st.cache_resource(show_spinner=False)
    def iniciar_banco(url):
        preparar(url, DB)
        return True
    try:
        iniciar_banco(DATABASE_URL)
    except Exception as exc:
        st.error('Não foi possível preparar o banco permanente. Nenhum dado local foi apagado por esta operação.')
        estado=getattr(exc,'sqlstate',None)
        detalhe=str(exc).lower()
        if 'password authentication failed' in detalhe or estado=='28P01':
            motivo='Senha do banco incorreta. Confira DB_PASSWORD nos Secrets.'
        elif 'tenant or user not found' in detalhe or 'tenant not found' in detalhe:
            motivo='Usuário ou endereço do pooler incorreto. Copie novamente a conexão Session pooler.'
        elif 'could not translate host' in detalhe or 'name or service not known' in detalhe:
            motivo='Endereço do servidor inválido ou DNS indisponível. Confira DB_HOST nos Secrets.'
        elif 'timeout' in detalhe or 'timed out' in detalhe or 'connection refused' in detalhe:
            motivo='Servidor indisponível ou tempo de conexão excedido. Confira o status no Supabase.'
        elif '[your-database-password]' in DATABASE_URL.lower():
            motivo='A senha provisória ainda está na cadeia de conexão.'
        elif isinstance(exc,ValueError) and 'conflito na migracao' in detalhe:
            motivo='Registros antigos conflitantes. É necessário revisar o SQLite antes de migrar.'
        elif estado=='23505':
            motivo='Existem registros duplicados na migração. Nenhum registro foi sobrescrito.'
        elif estado=='42501':
            motivo='Permissão insuficiente no banco de dados.'
        else:
            motivo='Falha de preparação: '+type(exc).__name__+(' (SQLSTATE '+estado+')' if estado else '')
        st.info(motivo)
        if st.button('Tentar conexão novamente'):
            st.rerun()
        st.stop()

def conectar():
    if DATABASE_URL:
        try:
            return conectar_postgres(DATABASE_URL)
        except Exception:
            st.error('Banco permanente indisponível. Nenhum registro será gravado localmente.')
            st.stop()

def consultar(sql='SELECT * FROM recibos ORDER BY id DESC',args=()):
    with conectar() as db:return db.execute(sql,args).fetchall()

def exibir(r):
    im=imagem(r); st.image(im,use_container_width=True)
    nome=f'Recibo_AP{r[1]}_{MESES[r[3]-1]}_{r[4]}_{r[0]:04d}'
    a,b=st.columns(2)
    a.download_button('Baixar JPG',exportar(im,'JPG'),nome+'.jpg','image/jpeg',key=f'jpg{r[0]}')
    b.download_button('Baixar PDF',exportar(im,'PDF'),nome+'.pdf','application/pdf',key=f'pdf{r[0]}')
    jpg=base64.b64encode(exportar(im,'JPG')).decode('ascii')
    msg=f"Olá! Segue o recibo nº {r[0]:04d} da taxa condominial do apartamento {r[1]}, referente a {MESES[r[3]-1]}/{r[4]}, no valor de {dinheiro(r[2])}."
    payload=json.dumps({'jpg':jpg,'nome':nome+'.jpg','msg':msg,'url':'https://wa.me/?text='+quote(msg)},ensure_ascii=True)
    components.html("""<button id="zap" style="background:#168348;color:white;border:0;border-radius:8px;padding:12px 20px;font:600 15px sans-serif;cursor:pointer">Enviar recibo pelo WhatsApp</button><p id="info" style="font:13px sans-serif;color:#59636b;margin:8px 0"></p><script>const p="""+payload+""";const raw=Uint8Array.from(atob(p.jpg),c=>c.charCodeAt(0));const file=new File([raw],p.nome,{type:'image/jpeg'});document.getElementById('zap').onclick=async()=>{const info=document.getElementById('info');try{if(navigator.canShare&&navigator.canShare({files:[file]})){await navigator.share({files:[file],text:p.msg});return;}}catch(e){if(e.name==='AbortError')return;}const a=document.createElement('a');a.href=URL.createObjectURL(file);a.download=p.nome;a.click();window.open(p.url,'_blank','noopener');info.textContent='Anexe o JPG baixado à conversa do WhatsApp e confirme o envio.';};</script>""",height=90)
    st.caption('No celular, escolha WhatsApp no menu de compartilhamento, se disponível. No computador, anexe o JPG baixado à conversa.')


def gerenciar(rs, chave):
    st.divider()
    st.subheader('Alterar ou excluir pagamentos')
    if not rs:
        st.info('Nenhum pagamento disponível neste filtro.')
        return
    registros={r[0]:r for r in rs}
    n=st.selectbox('Selecione o pagamento',list(registros),format_func=lambda i:f"Recibo {i:04d} | Apto {registros[i][1]} | {dinheiro(registros[i][2])} | {MESES[registros[i][3]-1]}/{registros[i][4]}",key=chave+'_selecionar')
    r=registros[n]
    k=f'{chave}_{n}'
    a,b=st.columns(2)
    if a.button('Alterar pagamento',key=k+'_alterar',use_container_width=True):
        st.session_state[chave+'_acao']=(n,'editar')
    if b.button('Excluir pagamento',key=k+'_excluir',use_container_width=True):
        st.session_state[chave+'_acao']=(n,'excluir')
    acao=st.session_state.get(chave+'_acao')
    if acao==(n,'editar'):
        with st.form(k+'_edicao'):
            opcoes=apts if r[1] in apts else [r[1]]+apts
            ap=st.selectbox('Apartamento',opcoes,index=opcoes.index(r[1]))
            v=st.number_input('Valor recebido (R$)',min_value=0.01,max_value=999999.99,value=r[2]/100,step=10.0,format='%.2f')
            a,b=st.columns(2)
            m=a.selectbox('Mês de referência',range(1,13),index=r[3]-1,format_func=lambda x:MESES[x-1].capitalize())
            y=b.number_input('Ano de referência',2000,2100,r[4])
            dt=st.date_input('Data do pagamento',value=date.fromisoformat(r[5]),format='DD/MM/YYYY')
            fo=st.radio('Forma de pagamento',['Dinheiro','Pix'],index=0 if r[6]=='Dinheiro' else 1,horizontal=True)
            salvar=st.form_submit_button('Salvar alterações',type='primary')
        if salvar:
            if ap not in apts or (ap!=r[1] and ap not in nomes):
                st.error('Selecione um apartamento válido.')
            else:
                cents=int((Decimal(str(v))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
                with conectar() as db:
                    db.execute('BEGIN IMMEDIATE')
                    existe=db.execute('SELECT id FROM recibos WHERE apt=? AND mes=? AND ano=? AND id<>?',(ap,m,y,n)).fetchone()
                    if existe:
                        st.warning('Já existe um pagamento para este apartamento e mês. Altere ou exclua o registro existente.')
                    else:
                        atual=db.execute('SELECT * FROM recibos WHERE id=?',(n,)).fetchone()
                        if atual!=r:
                            st.error('Este registro foi alterado por outra sessão. Atualize a página.')
                        else:
                            db.execute('UPDATE recibos SET apt=?,centavos=?,mes=?,ano=?,data=?,forma=?,nome=? WHERE id=?',(ap,cents,m,y,dt.isoformat(),fo,r[7] if ap==r[1] else nomes[ap],n))
                            db.commit()
                            st.session_state.pop(chave+'_acao',None)
                            st.session_state['aviso_gestao']='Pagamento alterado. Gere novamente o recibo e substitua cópias anteriores.'
                            st.rerun()
    elif acao==(n,'excluir'):
        st.warning(f'Excluir o recibo {n:04d} do apartamento {r[1]}? O registro será removido do controle e dos totais. Cópias já enviadas não serão canceladas automaticamente.')
        conf=st.checkbox('Confirmo a exclusão deste pagamento',key=k+'_conf')
        if st.button('Confirmar exclusão',key=k+'_confirmar',disabled=not conf,type='primary'):
            with conectar() as db:
                db.execute('BEGIN IMMEDIATE')
                atual=db.execute('SELECT * FROM recibos WHERE id=?',(n,)).fetchone()
                if atual!=r:
                    st.error('O registro mudou ou foi excluído. Atualize a página.')
                    return
                db.execute('DELETE FROM recibos WHERE id=?',(n,))
            if st.session_state.get('ultimo')==n:
                st.session_state.pop('ultimo',None)
            st.session_state.pop(chave+'_acao',None)
            st.session_state['aviso_gestao']='Pagamento excluído. Os totais foram atualizados.'
            st.rerun()
    if acao and st.button('Cancelar operação',key=k+'_cancelar'):
        st.session_state.pop(chave+'_acao',None)
        st.rerun()


def excluir_lote(rs):
    st.subheader('Excluir recibos do histórico')
    registros={r[0]:r for r in rs}
    todos=st.checkbox('Selecionar todos os recibos deste filtro',key='lote_todos')
    ids=st.multiselect('Selecione um ou mais recibos',list(registros),format_func=lambda i:f"Recibo {i:04d} | Apto {registros[i][1]} | {MESES[registros[i][3]-1]}/{registros[i][4]} | {dinheiro(registros[i][2])}",key='lote_ids',disabled=todos)
    escolhidos=list(registros) if todos else ids
    st.caption(f'{len(escolhidos)} recibo(s) selecionado(s).')
    if st.button('Excluir selecionados',disabled=not escolhidos,key='lote_preparar'):
        st.session_state['lote_pendente']=[registros[i] for i in escolhidos]
    pendentes=st.session_state.get('lote_pendente',[])
    if not pendentes:
        return
    st.warning(f'Confirme a exclusão definitiva de {len(pendentes)} recibo(s), no total de {dinheiro(sum(r[2] for r in pendentes))}. Os totais financeiros serão recalculados. Cópias já baixadas ou enviadas não serão canceladas.')
    st.table([{'Recibo':f'{r[0]:04d}','Apartamento':r[1],'Referência':f'{MESES[r[3]-1]}/{r[4]}','Valor':dinheiro(r[2])} for r in pendentes])
    a,b=st.columns(2)
    if a.button('Confirmar exclusão definitiva',type='primary',key='lote_confirmar'):
        with conectar() as db:
            db.execute('BEGIN IMMEDIATE')
            if any(db.execute('SELECT * FROM recibos WHERE id=?',(r[0],)).fetchone()!=r for r in pendentes):
                st.error('Um registro foi alterado ou excluído. Cancele e selecione novamente.')
                return
            db.executemany('DELETE FROM recibos WHERE id=?',[(r[0],) for r in pendentes])
        if st.session_state.get('ultimo') in {r[0] for r in pendentes}:
            st.session_state.pop('ultimo',None)
        st.session_state.pop('lote_pendente',None)
        st.session_state['limpar_lote']=True
        st.session_state['aviso_gestao']=f'{len(pendentes)} recibo(s) excluído(s).'
        st.rerun()
    if b.button('Cancelar exclusão',key='lote_cancelar'):
        st.session_state.pop('lote_pendente',None)
        st.rerun()

st.markdown('''<style>.stApp{background:#f5f7fa;color:#203b50} [data-testid="stSidebar"]{background:#e8eef4} div[data-testid="stMetric"]{background:#fff;border:1px solid #dce4eb;padding:16px;border-radius:12px} .block-container{max-width:1250px} </style>''',unsafe_allow_html=True)


hoje=date.today(); apts=[f'{andar}{porta:02d}' for andar in range(5) for porta in range(1,5)]
nomes=dict(consultar('SELECT apt,nome FROM moradores'))
if st.session_state.get('aviso_gestao'):
    st.success(st.session_state.pop('aviso_gestao'))
pagina=st.sidebar.radio('Menu',['Condôminos','Emitir recibo','Controle mensal','Histórico','Relatório financeiro'])
if pagina=='Condôminos':
    st.subheader('Cadastro de condôminos')
    apt = st.selectbox('Apartamento', apts)
    with st.form(f'cadastro_{apt}'):
        nome = st.text_input('Nome do condômino', value=nomes.get(apt, ''), max_chars=120)
        salvar = st.form_submit_button('Alterar cadastro' if apt in nomes else 'Salvar cadastro', type='primary')
    if salvar:
        if nome.strip():
            with conectar() as db:
                db.execute('INSERT INTO moradores(apt,nome) VALUES(?,?) ON CONFLICT(apt) DO UPDATE SET nome=excluded.nome', (apt, nome.strip()))
            nomes[apt] = nome.strip()
            st.success(f'Cadastro do apartamento {apt} salvo.')
        else:
            st.error('Digite o nome do condômino.')
    if apt in nomes:
        with st.expander('Excluir condômino'):
            confirmar = st.checkbox(f'Excluir {nomes[apt]} do apartamento {apt} e manter os recibos anteriores?', key=f'conf_{apt}_{nomes[apt]}')
            if st.button('Excluir cadastro', disabled=not confirmar):
                with conectar() as db:
                    db.execute('DELETE FROM moradores WHERE apt=? AND nome=?', (apt, nomes[apt]))
                st.rerun()
    st.table([{'Andar': 'Térreo' if a[0]=='0' else f'{a[0]}º andar', 'Apartamento': a, 'Condômino': nomes.get(a, 'Sem cadastro')} for a in apts])
elif pagina=='Emitir recibo':
    st.subheader('Registrar pagamento')
    apt = st.selectbox('Apartamento', apts, format_func=lambda a: f"{a} · {nomes.get(a, 'Sem cadastro')}")
    if apt not in nomes:
        st.info('Abra Condôminos e cadastre o nome para emitir o primeiro recibo desta unidade.')
        st.stop()
    with st.form(f'novo_{apt}',clear_on_submit=False):
        valor=st.number_input('Valor recebido (R$)',min_value=0.01,max_value=999999.99,value=None,step=10.0,format='%.2f')
        a,b,c=st.columns(3); mes=a.selectbox('Mês de referência',range(1,13),index=hoje.month-1,format_func=lambda x:MESES[x-1].capitalize()); ano=b.number_input('Ano de referência',min_value=2000,max_value=2100,value=hoje.year); data=c.date_input('Data do pagamento',value=hoje,format='DD/MM/YYYY')
        forma=st.radio('Forma de pagamento',['Dinheiro','Pix'],horizontal=True,index=1)
        confirma=st.checkbox('Confirmo que o valor foi efetivamente recebido.')
        enviar=st.form_submit_button('Registrar e gerar recibo',type='primary')
    if enviar:
        if valor is None:st.error('Informe o valor recebido.')
        elif not confirma:st.error('Confirme o recebimento antes de emitir.')
        else:
            cents=int((Decimal(str(valor))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
            with conectar() as db:
                db.execute('BEGIN IMMEDIATE')
                existe=db.execute('SELECT id FROM recibos WHERE apt=? AND mes=? AND ano=?',(apt,mes,ano)).fetchone()
                if db.execute('SELECT nome FROM moradores WHERE apt=?',(apt,)).fetchone()!=(nomes[apt],):st.warning('Confira o cadastro atualizado.')
                elif existe:st.warning('Já existe um recibo para este apartamento e mês. Altere ou exclua o registro pelo histórico.')
                else:
                    sql='INSERT INTO recibos(apt,centavos,mes,ano,data,forma,nome) VALUES(?,?,?,?,?,?,?)'
                    if DATABASE_URL:sql+=' RETURNING id'
                    cur=db.execute(sql,(apt,cents,mes,ano,data.isoformat(),forma,nomes[apt]))
                    novo_id=cur.fetchone()[0] if DATABASE_URL else cur.lastrowid
                    db.commit()
                    st.session_state['ultimo']=novo_id;st.success('Pagamento registrado com sucesso.')
    if st.session_state.get('ultimo'):
        ultimos=consultar('SELECT * FROM recibos WHERE id=?',(st.session_state['ultimo'],))
        if ultimos:exibir(ultimos[0])
        else:st.session_state.pop('ultimo',None)
elif pagina in ('Controle mensal','Relatório financeiro'):
    a,b=st.columns(2); ano=a.number_input('Ano',2000,2100,hoje.year); mes=b.selectbox('Mês',range(1,13),index=hoje.month-1,format_func=lambda x:MESES[x-1].capitalize())
    rs=consultar('SELECT * FROM recibos WHERE ano=? AND mes=?',(ano,mes)); pagos={r[1] for r in rs if r[1] in apts}; a,b,c=st.columns(3); a.metric('Total recebido',dinheiro(sum(r[2] for r in rs))); b.metric('Apartamentos com registro',f'{len(pagos)}/{len(apts)}');c.metric('Sem registro',len(apts)-len(pagos))
    if pagina=='Controle mensal':
        st.table([{'Apartamento':apt,'Condômino':nomes.get(apt,'Sem cadastro'),'Situação':'Com pagamento registrado' if apt in pagos else 'Sem registro','Total recebido':dinheiro(sum(r[2] for r in rs if r[1]==apt))} for apt in apts]);st.caption('Registro de pagamento não comprova quitação integral se houver pagamentos parciais.')
    else:
        st.table([{'Forma':f,'Recibos':sum(r[6]==f for r in rs),'Total':dinheiro(sum(r[2] for r in rs if r[6]==f))} for f in ['Dinheiro','Pix']]);st.bar_chart([{'Forma':f,'Total':sum(r[2] for r in rs if r[6]==f)/100} for f in ['Dinheiro','Pix']],x='Forma',y='Total')
    gerenciar(rs,'mensal' if pagina=='Controle mensal' else 'financeiro')
else:
    if st.session_state.pop('limpar_lote',False):
        st.session_state.pop('lote_ids',None)
        st.session_state.pop('lote_todos',None)
    st.subheader('Histórico de recibos'); filtro=st.selectbox('Apartamento',['Todos']+apts);rs=consultar() if filtro=='Todos' else consultar('SELECT * FROM recibos WHERE apt=? ORDER BY id DESC',(filtro,))
    if not rs:st.info('Nenhum pagamento registrado.')
    else:
        st.dataframe([{'Recibo':f'{r[0]:04d}','Apartamento':r[1],'Condômino':r[7],'Valor':dinheiro(r[2]),'Referência':f'{MESES[r[3]-1]}/{r[4]}','Data':'/'.join(r[5].split('-')[::-1]),'Forma':r[6]} for r in rs],hide_index=True,use_container_width=True)
        excluir_lote(rs)
        gerenciar(rs,'historico')
        n=st.selectbox('Selecionar recibo', [r[0] for r in rs],format_func=lambda i:f'Recibo {i:04d}');exibir(next(r for r in rs if r[0]==n))
if DATABASE_URL:
    st.sidebar.success('Banco permanente | PostgreSQL')
    with st.sidebar.expander('Backup dos registros'):
        if st.button('Preparar backup',key='preparar_backup'):
            rows=consultar()
            st.session_state['backup_gestao']=json.dumps({'versao':1,'colunas':['id','apt','centavos','mes','ano','data','forma','nome'],'moradores':nomes,'recibos':rows},ensure_ascii=False,indent=2).encode('utf-8')
        if st.session_state.get('backup_gestao'):
            st.download_button('Baixar backup JSON',st.session_state['backup_gestao'],file_name='backup_bloco_10.json',mime='application/json')
        st.caption('Guarde o arquivo em local seguro. A restauração ainda é manual.')
else:
    st.sidebar.warning('Banco local — não indicado para pagamentos reais no Streamlit Cloud.')
    st.sidebar.caption('Faça cópias de segurança do arquivo pagamentos.sqlite3 com o aplicativo fechado.')

