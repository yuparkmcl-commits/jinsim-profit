import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import datetime, os

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    KOREAN_FONT = 'Helvetica'
    for fp in ['malgun.ttf','C:/Windows/Fonts/malgun.ttf','/System/Library/Fonts/AppleGothic.ttf']:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('KF', fp))
                KOREAN_FONT = 'KF'
                break
            except: pass
    REPORTLAB_OK = True
except: REPORTLAB_OK = False

st.set_page_config(page_title="진심카스테라 수익 분석기", page_icon="🍰", layout="wide")
st.markdown("""
<style>
/* Streamlit 하단 브랜딩 완전 숨기기 */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}
div[data-testid="stToolbar"] {display: none !important;}
div[data-testid="stDecoration"] {display: none !important;}
div[data-testid="stStatusWidget"] {display: none !important;}
.viewerBadge_container__1QSob {display: none !important;}
.styles_viewerBadge__1yB5_ {display: none !important;}
[data-testid="manage-app-button"] {display: none !important;}
button[kind="manage"] {display: none !important;}
.stAppDeployButton {display: none !important;}
div[class*="manageApp"] {display: none !important;}
div[class*="manage-app"] {display: none !important;}

.section-label{font-size:.82rem;font-weight:700;letter-spacing:.06em;color:#fff;background:#0F6E56;padding:4px 12px;border-radius:6px;display:inline-block;margin-bottom:.6rem;margin-top:1.4rem;}
.result-card{border-radius:16px;padding:1.6rem;text-align:center;color:white;margin-bottom:1rem;}
.result-card .label{font-size:.85rem;opacity:.8;margin-bottom:.3rem;}
.result-card .value{font-size:2.2rem;font-weight:700;}
.result-card .sub{font-size:.82rem;opacity:.7;margin-top:.3rem;}
.detail-block{border:1px solid rgba(128,128,128,.2);border-radius:12px;padding:1rem 1.2rem;margin-bottom:.8rem;}
.detail-title{font-size:.82rem;font-weight:600;color:#0F6E56;margin-bottom:.6rem;padding-bottom:.4rem;border-bottom:.5px solid rgba(128,128,128,.15);}
.detail-row{display:flex;justify-content:space-between;padding:.25rem 0;font-size:.88rem;}
.detail-row.sub{padding-left:1rem;color:#888;font-size:.82rem;}
.detail-row.total{font-weight:700;border-top:.5px solid rgba(128,128,128,.2);margin-top:.3rem;padding-top:.5rem;}
.pos{color:#0F6E56;}.neg{color:#dc2626;}
.badge{display:inline-block;font-size:.72rem;padding:2px 8px;border-radius:20px;margin-left:6px;font-weight:600;}
.badge-green{background:#E1F5EE;color:#085041;}
.badge-amber{background:#FEF3C7;color:#92400E;}
.badge-blue{background:#E6F1FB;color:#0C447C;}
.badge-purple{background:#EEEDFE;color:#3C3489;}
.badge-coral{background:#FAECE7;color:#712B13;}
.badge-warn{background:#FEF3C7;color:#92400E;}
.badge-ok{background:#E1F5EE;color:#085041;}
.fee-card{border:1px solid rgba(128,128,128,.2);border-radius:12px;padding:.8rem 1rem;text-align:center;}
.fee-card .fc-label{font-size:.75rem;color:#888;margin-bottom:.3rem;}
.fee-card .fc-pct{font-size:1.4rem;font-weight:700;}
.fee-card .fc-amt{font-size:.75rem;color:#888;margin-top:.2rem;}
.fee-card .fc-cmp{font-size:.72rem;padding:2px 6px;border-radius:10px;display:inline-block;margin-top:.3rem;}
.insight-box{border-left:3px solid #f59e0b;background:#fffbeb;border-radius:0 8px 8px 0;padding:.7rem 1rem;margin-bottom:.6rem;font-size:.85rem;color:#78350f;}
.insight-good{border-left-color:#10b981;background:#ecfdf5;color:#065f46;}
.notice-box{background:rgba(128,128,128,.08);border-radius:8px;padding:.7rem 1rem;font-size:.8rem;color:#888;margin-bottom:.8rem;}
.kpi-card{background:var(--background-color,#f9fafb);border:1px solid rgba(128,128,128,.2);border-radius:12px;padding:1rem;text-align:center;}
.kpi-card .kc-label{font-size:.75rem;color:#888;margin-bottom:.3rem;}
.kpi-card .kc-value{font-size:1.2rem;font-weight:700;}
.kpi-card .kc-sub{font-size:.73rem;color:#888;margin-top:.3rem;line-height:1.4;}
.sim-row{display:flex;justify-content:space-between;align-items:center;padding:.3rem 0;font-size:.88rem;border-bottom:.5px solid rgba(128,128,128,.1);}
.hangul-hint{font-size:.78rem;color:#0F6E56;margin-top:2px;margin-bottom:6px;padding-left:2px;}
.insurance-box{background:rgba(15,110,86,.08);border:1px solid rgba(15,110,86,.2);border-radius:8px;padding:.7rem 1rem;margin-top:.3rem;font-size:.82rem;}
</style>
""", unsafe_allow_html=True)

# ── 한글 금액 변환 ────────────────────────────────────────────────────
def num_to_korean(n):
    if n == 0: return "0원"
    n = int(n)
    units = ["", "만", "억", "조"]
    result = ""
    unit_idx = 0
    while n > 0:
        part = n % 10000
        if part != 0:
            result = f"{part:,}{units[unit_idx]} " + result
        n //= 10000
        unit_idx += 1
    return result.strip() + "원"

def fmt(v, sign=True):
    return f"{v:+,.0f}원" if sign else f"{v:,.0f}원"

def ps(df, ci):
    if ci is None: return 0.0
    return pd.to_numeric(df.iloc[:,ci], errors='coerce').fillna(0).sum()

def find_col(df_h, keyword, exclude=None, use_last=False):
    found = []
    for ci in range(df_h.shape[1]):
        for ri in range(df_h.shape[0]):
            v = df_h.iloc[ri,ci]
            if isinstance(v,str) and keyword in v:
                if exclude is None or exclude not in v:
                    found.append(ci); break
    if not found: return None
    return found[-1] if use_last else found[0]

def detail_row(label, val, sub=False, total=False, per_unit=None, pct=None):
    cls = "detail-row" + (" sub" if sub else "") + (" total" if total else "")
    vc  = "pos" if val >= 0 else "neg"
    if per_unit is not None or pct is not None:
        parts = []
        if per_unit is not None: parts.append(f"건당 {abs(per_unit):,.0f}원")
        if pct is not None: parts.append(f"{pct:.1f}%")
        sub_txt = " · ".join(parts)
        return (f'<div class="{cls}" style="align-items:flex-start;">'
                f'<span>{label}</span>'
                f'<div style="text-align:right;">'
                f'<div class="{vc}">{fmt(val)}</div>'
                f'<div style="font-size:.75rem;color:#888;">{sub_txt}</div>'
                f'</div></div>')
    return f'<div class="{cls}"><span>{label}</span><span class="{vc}">{fmt(val)}</span></div>'

# ── 파싱 함수 ─────────────────────────────────────────────────────────
def parse_baemin(file):
    try:
        df_h=pd.read_excel(file,header=None,nrows=5)
        df  =pd.read_excel(file,header=None,skiprows=5)
        cF=find_col(df_h,'바로결제주문금액'); cG=find_col(df_h,'만나서결제주문금액')
        cO=find_col(df_h,'만나서결제배달팁',exclude='배민'); cAE=find_col(df_h,'입금금액')
        cI=find_col(df_h,'배민1중개이용료'); cJ=find_col(df_h,'알뜰배달 중개이용료')
        cK=find_col(df_h,'가게배달중개이용료'); cL=find_col(df_h,'픽업중개이용료')
        cV=find_col(df_h,'기본수수료(정률)'); cW=find_col(df_h,'우대수수료')
        cAA=find_col(df_h,'(E) 부가세'); cT=find_col(df_h,'배민1 한집배달 배달비')
        cU=find_col(df_h,'알뜰배달 배달비'); cAB=find_col(df_h,'우리가게클릭 이용요금')
        cM=find_col(df_h,'주문금액 즉시할인')
        if cAE is None: return None,"AE열(입금금액)을 찾을 수 없습니다."
        sF=ps(df,cF); sG=ps(df,cG); sO=ps(df,cO); sAE=ps(df,cAE)
        총매출=sF+sG
        중개수수료=ps(df,cI)+ps(df,cJ)+ps(df,cK)+ps(df,cL)
        결제수수료=ps(df,cV)+ps(df,cW); 부가세=ps(df,cAA)
        배달비=ps(df,cT)+ps(df,cU); 광고비=ps(df,cAB); 즉시할인=ps(df,cM)
        순이익=sAE+sG+sO
        진짜수수료=총매출-순이익 if 총매출>0 else 0
        return {'순이익':순이익,'AE정산':sAE,'G만나서식대':sG,'O만나서배달팁':sO,
                '총매출':총매출,'주문건수':0,'객단가':0,
                '중개수수료':중개수수료,'결제수수료':결제수수료,'부가세':부가세,
                '배달비':배달비,'광고비':광고비,'즉시할인':즉시할인,
                '진짜수수료율':진짜수수료/총매출 if 총매출>0 else 0}, None
    except Exception as e: return None,f"파일 읽기 오류: {e}"

def parse_coupang(file):
    try:
        df_h=pd.read_excel(file,header=None,nrows=3)
        df  =pd.read_excel(file,header=None,skiprows=3)
        cAN=None
        for c in range(df_h.shape[1]):
            if isinstance(df_h.iloc[0,c],str) and '정산금액' in df_h.iloc[0,c]:
                for c2 in range(c,df_h.shape[1]):
                    if isinstance(df_h.iloc[1,c2],str) and '산정후' in df_h.iloc[1,c2]:
                        cAN=c2
                break
        if cAN is None: cAN=find_col(df_h,'산정후',use_last=True)
        if cAN is None: return None,"AN열을 찾을 수 없습니다."
        k_s=pd.to_numeric(df.iloc[:,10],errors='coerce').fillna(0)
        mask_pos=k_s>0
        v_s=pd.to_numeric(df.iloc[:,21],errors='coerce').fillna(0)
        배달비=float(v_s.sum())
        배달비_무료건수=int((v_s[mask_pos]==0).sum())
        sAN=ps(df,cAN); 총매출=ps(df,10)
        중개수수료=ps(df,16); 결제수수료=ps(df,17)
        광고비=ps(df,36); 상점쿠폰=ps(df,13); 즉시할인=ps(df,22)+ps(df,23)
        주문건수=int(mask_pos.sum())
        진짜수수료율=(총매출-sAN)/총매출 if 총매출>0 else 0
        유료건수=주문건수-배달비_무료건수
        건당배달비=배달비/유료건수 if 유료건수>0 else 0
        try:
            data_pos=df[mask_pos].copy()
            data_pos['_hour']=pd.to_datetime(data_pos.iloc[:,1],errors='coerce').dt.hour
            data_pos['_wd']=pd.to_datetime(data_pos.iloc[:,1],errors='coerce').dt.dayofweek
            data_pos['_amt']=pd.to_numeric(data_pos.iloc[:,10],errors='coerce').fillna(0)
            시간대=data_pos.groupby('_hour')['_amt'].count().to_dict()
            요일별=data_pos.groupby('_wd')['_amt'].count().to_dict()
            _hm_raw=data_pos.groupby(['_wd','_hour'])['_amt'].count().unstack(fill_value=0)
            히트맵={int(wd):{int(h):int(v) for h,v in row.items()} for wd,row in _hm_raw.iterrows()}
        except: 시간대={}; 요일별={}; 히트맵={}
        return {'순이익':sAN,'총매출':총매출,'주문건수':주문건수,
                '객단가':총매출/주문건수 if 주문건수 else 0,
                '중개수수료':중개수수료,'결제수수료':결제수수료,
                '배달비':배달비,'배달비_무료건수':배달비_무료건수,'건당배달비':건당배달비,
                '광고비':광고비,'상점쿠폰':상점쿠폰,'즉시할인':즉시할인,
                '진짜수수료율':진짜수수료율,
                '시간대':시간대,'요일별':요일별,'히트맵':히트맵}, None
    except Exception as e: return None,f"파일 읽기 오류: {e}"

def parse_yogiyo(file):
    try:
        df=pd.read_excel(file,header=None)
        data=df.iloc[2:].copy(); data=data[data.iloc[:,2]=='주문']
        def yg(ci): return pd.to_numeric(data.iloc[:,ci],errors='coerce').fillna(0).sum()
        총매출=yg(7); 타임딜=yg(13); 쿠폰=yg(14)
        중개=yg(19); 결제=yg(21); 배달대행=yg(23); 타임딜이용=yg(24); 광고=yg(25)
        순이익=총매출-(타임딜+쿠폰)-(중개+결제+배달대행+타임딜이용+광고)
        주문건수=len(data)
        진짜수수료율=(총매출-순이익)/총매출 if 총매출>0 else 0
        return {'순이익':순이익,'총매출':총매출,'주문건수':주문건수,
                '객단가':총매출/주문건수 if 주문건수 else 0,
                '타임딜할인':타임딜,'쿠폰할인':쿠폰,
                '중개이용료':중개,'결제이용료':결제,
                '배달대행이용료':배달대행,'타임딜이용료':타임딜이용,'광고비':광고,
                '진짜수수료율':진짜수수료율}, None
    except Exception as e: return None,f"파일 읽기 오류: {e}"

def parse_ddanggyeo(file):
    try:
        df=pd.read_excel(file,header=None,engine='xlrd')
        순이익=float(df.iloc[5,2]); 총매출=float(df.iloc[5,0])
        last=df.iloc[-1]
        def lv(c):
            v=last.iloc[c]
            return float(v) if pd.notna(v) and isinstance(v,(int,float)) else 0.0
        중개=abs(lv(28)); 결제=abs(lv(29))
        배달대행=lv(18); 사장님쿠폰=abs(lv(31)); 프로모션=abs(lv(32))
        data=df.iloc[39:69].copy()
        주문건수=int((data.iloc[:,12]=='승인').sum())
        진짜수수료율=(총매출-순이익)/총매출 if 총매출>0 else 0
        return {'순이익':순이익,'총매출':총매출,'주문건수':주문건수,
                '객단가':총매출/주문건수 if 주문건수 else 0,
                '중개이용료':중개,'결제정산이용료':결제,
                '배달대행이용료':배달대행,'사장님쿠폰':사장님쿠폰,'프로모션부담':프로모션,
                '진짜수수료율':진짜수수료율}, None
    except Exception as e: return None,f"파일 읽기 오류: {e}"

def parse_naver(file):
    try:
        df=pd.read_excel(file)
        일반=df[df['정산상태']=='일반정산']
        취소=df[df['정산상태']=='정산후 취소']
        총매출=일반[일반['수수료 구분']=='예약 매출연동 수수료']['수수료 기준금액'].sum()
        취소매출=취소[취소['수수료 구분']=='예약 매출연동 수수료']['수수료 기준금액'].sum()
        수수료=일반['수수료금액'].sum(); 취소수수료=취소['수수료금액'].sum()
        순이익=총매출+취소매출+수수료+취소수수료
        주문건수=int(일반[일반['수수료 구분']=='예약 매출연동 수수료']['수수료 기준금액'].count())
        진짜수수료율=(총매출-순이익)/총매출 if 총매출>0 else 0
        return {'순이익':순이익,'총매출':총매출,'취소매출':취소매출,
                '주문건수':주문건수,'객단가':총매출/주문건수 if 주문건수 else 0,
                'Npay수수료':수수료+취소수수료,'진짜수수료율':진짜수수료율}, None
    except Exception as e: return None,f"파일 읽기 오류: {e}"

def parse_prev_excel(file):
    try:
        df=pd.read_excel(file,sheet_name='비교데이터',index_col=0)
        return df.to_dict()['값'],None
    except Exception as e: return None,f"전월 파일 오류: {e}"

# ── 엑셀 생성 ─────────────────────────────────────────────────────────
def generate_excel(data):
    buf=BytesIO()
    with pd.ExcelWriter(buf,engine='xlsxwriter') as writer:
        wb=writer.book
        fh=wb.add_format({'bold':True,'font_size':13,'font_color':'#085041','bottom':2,'bottom_color':'#0F6E56'})
        fhd=wb.add_format({'bold':True,'bg_color':'#0F6E56','font_color':'white','border':1,'border_color':'#cccccc','align':'center'})
        fm=wb.add_format({'num_format':'#,##0"원"','border':1,'border_color':'#eeeeee'})
        fp=wb.add_format({'num_format':'0.00"%"','border':1,'border_color':'#eeeeee'})
        fl=wb.add_format({'border':1,'border_color':'#eeeeee','bg_color':'#f9fafb'})
        ft=wb.add_format({'bold':True,'bg_color':'#E1F5EE','num_format':'#,##0"원"','border':1,'border_color':'#cccccc'})
        fn=wb.add_format({'num_format':'#,##0"원"','font_color':'#dc2626','border':1,'border_color':'#eeeeee'})
        today=data.get('month_str', datetime.date.today().strftime('%Y년 %m월'))
        ws1=wb.add_worksheet('📊 요약')
        ws1.set_column('A:A',28); ws1.set_column('B:B',18)
        ws1.write('A1',f'진심카스테라 수익 분석 — {today}',fh)
        ws1.write('A2','※ 현금흐름 기준 추정치')
        ws1.write_row('A4',['항목','금액'],fhd)
        rows=[('총 매출 (배달+오프라인)',data['total_gross']),
              ('플랫폼 실수령액 합계',data['platform_sum']),
              ('오프라인 실수령액',data['pos_sales']-data['pos_card_fee']),
              ('포스기 카드수수료',-data['pos_card_fee']),
              ('고정비 합계 (4대보험 포함)',-data['fixed_total']),
              ('변동비 합계',-data['var_total'])]
        r=4
        for label,val in rows:
            ws1.write(r,0,label,fl); ws1.write(r,1,val,fm if val>=0 else fn); r+=1
        ws1.write(r,0,'★ 최종 순이익',ft); ws1.write(r,1,data['final'],ft); r+=1
        ws1.write(r,0,'영업이익률',fl); ws1.write(r,1,data['margin']/100,fp); r+=2
        ws1.write(r,0,'플랫폼 총 수수료',fl); ws1.write(r,1,-data['total_platform_fee'],fn); r+=1
        ws1.write(r,0,'손익분기점',fl); ws1.write(r,1,data['bep'],fm)
        ws2=wb.add_worksheet('🏪 플랫폼별')
        ws2.set_column('A:A',24); ws2.set_column('B:H',16)
        ws2.write('A1','플랫폼별 수익 상세',fh)
        ws2.write_row('A3',['플랫폼','총매출','진짜수수료율','실수령액','100원팔면남는돈','건수','객단가'],fhd)
        r=3
        변동비율=data['변동비율']
        for name,d in data['platforms'].items():
            if d and d['총매출']>0:
                fr=d['진짜수수료율']; cr=1-fr-변동비율
                ws2.write(r,0,name,fl); ws2.write(r,1,d['총매출'],fm)
                ws2.write(r,2,fr,fp); ws2.write(r,3,d['순이익'],fm)
                ws2.write(r,4,cr,fp); ws2.write(r,5,d['주문건수'],fl)
                ws2.write(r,6,d['객단가'],fm); r+=1
        ws3=wb.add_worksheet('💰 비용내역')
        ws3.set_column('A:A',12); ws3.set_column('B:B',26); ws3.set_column('C:C',16)
        ws3.write('A1','비용 내역',fh)
        ws3.write_row('A3',['구분','항목','금액'],fhd)
        r=3
        for item,val in data['fixed_items']:
            if val>0:
                ws3.write(r,0,'고정비',fl); ws3.write(r,1,item,fl); ws3.write(r,2,-val,fn); r+=1
        ws3.write(r,0,'',ft); ws3.write(r,1,'고정비 합계',ft); ws3.write(r,2,-data['fixed_total'],ft); r+=2
        for item,val in data['var_items']:
            if val>0:
                ws3.write(r,0,'변동비',fl); ws3.write(r,1,item,fl); ws3.write(r,2,-val,fn); r+=1
        ws3.write(r,0,'',ft); ws3.write(r,1,'변동비 합계',ft); ws3.write(r,2,-data['var_total'],ft)
        ws4=wb.add_worksheet('비교데이터')
        compare={
            '분析월':data.get('month_str', today),'총매출':data['total_gross'],
            '플랫폼실수령액':data['platform_sum'],'총수수료':data['total_platform_fee'],
            '최종순이익':data['final'],'영업이익률':data['margin'],
            '총주문건수':data['total_orders'],'평균객단가':data['avg_price'],
            '고정비':data['fixed_total'],'변동비':data['var_total'],'변동비율':변동비율,
            '포스기매출':data.get('pos_sales',0),
        }
        # 변동비 세부 항목 저장
        for item,val in data['var_items']:
            compare[f'변동비_{item}']=val
        for name,d in data['platforms'].items():
            compare[f'{name}순이익']=d['순이익'] if d else 0
            compare[f'{name}수수료율']=d['진짜수수료율']*100 if d else 0
            compare[f'{name}매출']=d['총매출'] if d else 0
        ws4.write_row('A1',['항목','값'],fhd)
        for i,(k,v) in enumerate(compare.items()):
            ws4.write(i+1,0,k,fl); ws4.write(i+1,1,v)
        ws4.set_column('A:B',22)
    return buf.getvalue()

def generate_pdf(data):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=15*mm,leftMargin=15*mm,topMargin=15*mm,bottomMargin=15*mm)
    kf=KOREAN_FONT
    ts=ParagraphStyle('t',fontName=kf,fontSize=15,spaceAfter=6,textColor=colors.HexColor('#085041'))
    ss=ParagraphStyle('s',fontName=kf,fontSize=9,spaceAfter=10,textColor=colors.grey)
    hs=ParagraphStyle('h',fontName=kf,fontSize=11,spaceAfter=6,textColor=colors.HexColor('#0F6E56'))
    ns=ParagraphStyle('n',fontName=kf,fontSize=8,textColor=colors.grey)
    story=[]
    today=data.get('month_str', datetime.date.today().strftime('%Y년 %m월'))
    story.append(Paragraph(f"진심카스테라 수익 분석 리포트 — {today}",ts))
    story.append(Paragraph("현금흐름 기준 추정치",ss))
    story.append(HRFlowable(width="100%",thickness=1,color=colors.HexColor('#0F6E56')))
    story.append(Spacer(1,8))
    story.append(Paragraph("핵심 지표",hs))
    t1=Table([['항목','금액'],
              ['총 매출',f"{data['total_gross']:,.0f}원"],
              ['플랫폼 총 수수료',f"-{data['total_platform_fee']:,.0f}원"],
              ['고정비 (4대보험 포함)',f"-{data['fixed_total']:,.0f}원"],
              ['변동비',f"-{data['var_total']:,.0f}원"],
              ['★ 최종 순이익',f"{data['final']:,.0f}원"],
              ['영업이익률',f"{data['margin']:.1f}%"],
              ['손익분기점',f"{data['bep']:,.0f}원"]],
             colWidths=[80*mm,80*mm])
    t1.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),kf),('FONTSIZE',(0,0),(-1,-1),9),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0F6E56')),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('BACKGROUND',(0,5),(-1,5),colors.HexColor('#E1F5EE')),
        ('GRID',(0,0),(-1,-1),.5,colors.HexColor('#cccccc')),('ALIGN',(1,0),(1,-1),'RIGHT'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9fafb')]),]))
    story.append(t1); story.append(Spacer(1,10))
    story.append(Paragraph("플랫폼별 수익",hs))
    pf_rows=[['플랫폼','총매출','수수료율','실수령액','100원팔면남는돈','건수']]
    변동비율=data['변동비율']
    for name,d in data['platforms'].items():
        if d and d['총매출']>0:
            fr=d['진짜수수료율']; cr=1-fr-변동비율
            pf_rows.append([name,f"{d['총매출']:,.0f}원",f"{fr*100:.1f}%",
                           f"{d['순이익']:,.0f}원",f"{cr*100:.1f}원",f"{d['주문건수']}건"])
    t2=Table(pf_rows,colWidths=[25*mm,33*mm,22*mm,33*mm,22*mm,15*mm])
    t2.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),kf),('FONTSIZE',(0,0),(-1,-1),8),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0F6E56')),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),.5,colors.HexColor('#cccccc')),('ALIGN',(1,0),(-1,-1),'RIGHT'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9fafb')]),]))
    story.append(t2); story.append(Spacer(1,6))
    story.append(HRFlowable(width="100%",thickness=.5,color=colors.grey))
    story.append(Paragraph("※ 현금흐름 기준 추정치입니다.",ns))
    doc.build(story)
    return buf.getvalue()

# ── UI ────────────────────────────────────────────────────────────────
st.title("🍰 진심카스테라 가맹점 수익 분석기")
st.caption("배달 플랫폼 정산 파일을 업로드하면 실질 순이익을 자동 계산합니다.")
st.markdown('<div class="notice-box">⚠️ 이 수치는 현금흐름 기준 추정치입니다. 재고 구매 등 일시적 지출이 포함된 달은 실제 영업이익과 차이가 날 수 있습니다.</div>',unsafe_allow_html=True)
st.divider()

left,right=st.columns([1.05,1],gap="large")

with left:
    st.markdown('<p class="section-label">① 플랫폼 정산 파일 업로드</p>',unsafe_allow_html=True)
    with st.expander("📂 이번 달 파일 업로드 (클릭하여 열기)",expanded=True):
        baemin_file =st.file_uploader("🟢 배달의민족 (.xlsx)",type=["xlsx"],key="baemin")
        coupang_file=st.file_uploader("🟠 쿠팡이츠 (.xlsx)",type=["xlsx"],key="coupang")
        yogiyo_file =st.file_uploader("🔴 요기요 주문별 정산 (.xlsx)",type=["xlsx"],key="yogiyo")
        ddang_file  =st.file_uploader("🟣 땡겨요 정산내역 (.xls)",type=["xls","xlsx"],key="ddang")
        naver_file  =st.file_uploader("🟢 네이버 수수료상세 (.xlsx)",type=["xlsx"],key="naver")

    st.markdown('<p class="section-label">⑥ 월별 비교 & 추이</p>',unsafe_allow_html=True)
    st.caption("저장 엑셀을 올리면 전월 비교 + 추이 그래프가 자동 생성됩니다.")
    monthly_files_left=st.file_uploader("저장 엑셀 업로드 (여러 개 가능)",
                                         type=["xlsx"],accept_multiple_files=True,key="monthly_left")
    show_prev=bool(monthly_files_left)
    prev_data=None
    if monthly_files_left:
        latest = sorted(monthly_files_left, key=lambda f: f.name)[-1]
        prev_data, prev_err = parse_prev_excel(latest)
        if prev_err: st.error(prev_err)

    st.markdown('<p class="section-label">② 데이터 기준월</p>',unsafe_allow_html=True)
    col_y, col_m = st.columns(2)
    with col_y:
        data_year = st.number_input("연도", min_value=2020, max_value=2030,
                                    value=datetime.date.today().year, step=1, format="%d")
    with col_m:
        data_month = st.number_input("월", min_value=1, max_value=12,
                                     value=datetime.date.today().month-1 if datetime.date.today().month>1 else 12,
                                     step=1, format="%d")
    data_month_str = f"{data_year}년 {data_month:02d}월"

    st.markdown('<p class="section-label">③ 오프라인 매출</p>',unsafe_allow_html=True)
    pos_sales=st.number_input("포스기 매출 (원)",min_value=0,value=0,step=10000,format="%d",help="카드수수료 1.1% 자동 차감")
    if pos_sales > 0:
        st.markdown(f'<div class="hangul-hint">→ {num_to_korean(pos_sales)}</div>', unsafe_allow_html=True)

    # ── ④ 고정비 ──────────────────────────────────────────────────────
    st.markdown('<p class="section-label">④ 고정비</p>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        rent=st.number_input("월세 (원)",min_value=0,value=0,step=10000,format="%d")
        if rent > 0:
            st.markdown(f'<div class="hangul-hint">→ {num_to_korean(rent)}</div>', unsafe_allow_html=True)
        manage=st.number_input("관리비 (원)",min_value=0,value=0,step=10000,format="%d")
        if manage > 0:
            st.markdown(f'<div class="hangul-hint">→ {num_to_korean(manage)}</div>', unsafe_allow_html=True)
        labor=st.number_input("인건비 합계 (세전, 원)",min_value=0,value=0,step=10000,format="%d")
        if labor > 0:
            st.markdown(f'<div class="hangul-hint">→ {num_to_korean(labor)}</div>', unsafe_allow_html=True)
    with c2:
        # ✅ 수정3: 기장료, 포스기유지비 추가
        jangryeo=st.number_input("기장료 (세무사비, 원)",min_value=0,value=0,step=10000,format="%d")
        if jangryeo > 0:
            st.markdown(f'<div class="hangul-hint">→ {num_to_korean(jangryeo)}</div>', unsafe_allow_html=True)
        pos_maint=st.number_input("포스기 유지비 (원)",min_value=0,value=0,step=10000,format="%d")
        if pos_maint > 0:
            st.markdown(f'<div class="hangul-hint">→ {num_to_korean(pos_maint)}</div>', unsafe_allow_html=True)

    # ✅ 수정4: 4대보험 자동계산 (회사부담 10.5%)
    insurance = int(labor * 0.105)
    if labor > 0:
        st.markdown(f"""
        <div class="insurance-box">
        💡 <b>4대보험 자동계산 (회사부담 10.5%)</b><br>
        &nbsp;&nbsp;직원 부담분: 약 {int(labor*0.105):,}원 (직원 월급에서 차감)<br>
        &nbsp;&nbsp;회사 부담분: 약 {insurance:,}원 → <b>고정비에 자동 포함</b><br>
        &nbsp;&nbsp;실제 인건비 총지출: <b>{int(labor + insurance):,}원</b> ({num_to_korean(labor + insurance)})
        </div>""", unsafe_allow_html=True)

    # ✅ 고정비 합계 = 입력값 그대로 + 4대보험 회사부담분
    fixed_total = rent + manage + labor + insurance + jangryeo + pos_maint
    st.info(f"💼 고정비 합계 (4대보험 포함): **{fixed_total:,}원** ({num_to_korean(fixed_total)})")

    st.markdown('<p class="section-label">⑤ 변동비</p>',unsafe_allow_html=True)
    c3,c4=st.columns(2)
    with c3:
        dongwon=st.number_input("동원 물류비",min_value=0,value=0,step=10000,format="%d")
        if dongwon>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(dongwon)}</div>',unsafe_allow_html=True)
        manwol=st.number_input("만월상회 (음료원액)",min_value=0,value=0,step=10000,format="%d")
        if manwol>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(manwol)}</div>',unsafe_allow_html=True)
        eggs=st.number_input("계란",min_value=0,value=0,step=10000,format="%d")
        if eggs>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(eggs)}</div>',unsafe_allow_html=True)
        boxes=st.number_input("포장박스",min_value=0,value=0,step=10000,format="%d")
        if boxes>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(boxes)}</div>',unsafe_allow_html=True)
    with c4:
        delivery_agency=st.number_input("배달대행비",min_value=0,value=0,step=10000,format="%d",help="배민·요기요 가게배달 + 땡겨요 배달대행비")
        if delivery_agency>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(delivery_agency)}</div>',unsafe_allow_html=True)
        consumables=st.number_input("소모품 카드결제",min_value=0,value=0,step=10000,format="%d")
        if consumables>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(consumables)}</div>',unsafe_allow_html=True)
        card_fee_etc=st.number_input("기타 카드수수료",min_value=0,value=0,step=10000,format="%d")
        if card_fee_etc>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(card_fee_etc)}</div>',unsafe_allow_html=True)
        ad_cost=st.number_input("광고비 (SNS 등)",min_value=0,value=0,step=10000,format="%d")
        if ad_cost>0: st.markdown(f'<div class="hangul-hint">→ {num_to_korean(ad_cost)}</div>',unsafe_allow_html=True)

    var_total=dongwon+manwol+eggs+boxes+delivery_agency+consumables+card_fee_etc+ad_cost
    st.info(f"📦 변동비 합계: **{var_total:,}원** ({num_to_korean(var_total)})")

with right:
    bd,bd_err=parse_baemin(baemin_file)   if baemin_file  else (None,None)
    cp,cp_err=parse_coupang(coupang_file) if coupang_file else (None,None)
    yg,yg_err=parse_yogiyo(yogiyo_file)   if yogiyo_file  else (None,None)
    dg,dg_err=parse_ddanggyeo(ddang_file) if ddang_file   else (None,None)
    nv,nv_err=parse_naver(naver_file)     if naver_file   else (None,None)
    for err,label in [(bd_err,'배민'),(cp_err,'쿠팡'),(yg_err,'요기요'),(dg_err,'땡겨요'),(nv_err,'네이버')]:
        if err: st.error(f"{label} 오류: {err}")

    baemin_orders=st.session_state.get("baemin_orders",0)

    bd_p=bd['순이익'] if bd else 0
    cp_p=cp['순이익'] if cp else 0
    yg_p=yg['순이익'] if yg else 0
    dg_p=dg['순이익'] if dg else 0
    nv_p=nv['순이익'] if nv else 0

    pos_card_fee=pos_sales*0.011
    pos_net=pos_sales-pos_card_fee
    platform_sum=bd_p+cp_p+yg_p+dg_p+nv_p
    total_rev=platform_sum+pos_net
    total_cost=fixed_total+var_total
    final=total_rev-total_cost
    margin=(final/total_rev*100) if total_rev>0 else 0

    delivery_gross=sum([x['총매출'] for x in [bd,cp,yg,dg,nv] if x])
    total_gross=delivery_gross+pos_sales
    delivery_orders=(baemin_orders if bd else 0)+sum([x['주문건수'] for x in [cp,yg,dg] if x])
    delivery_sales=sum([x['총매출'] for x in [bd,cp,yg,dg] if x])
    total_orders=delivery_orders
    avg_price=delivery_sales/delivery_orders if delivery_orders else 0
    total_platform_fee=sum([(x['총매출']-x['순이익']) for x in [bd,cp,yg,dg,nv] if x])+pos_card_fee

    변동비율=var_total/total_gross if total_gross>0 else 0
    전체수수료율=(total_gross-total_rev)/total_gross if total_gross>0 else 0
    공헌이익률=1-전체수수료율-변동비율
    bep=fixed_total/공헌이익률 if 공헌이익률>0 else 0

    # 재료비율 (배달대행비·광고비 제외 순수 재료비)
    재료비=dongwon+manwol+eggs+boxes
    재료비율=재료비/total_gross if total_gross>0 else 0

    # 땡겨요 실질 수수료율 (배달대행비 포함)
    if dg and dg['총매출']>0:
        dg_실질수수료율=(dg['총매출']-(dg['순이익']-dg['배달대행이용료']))/dg['총매출']
        dg['실질수수료율']=dg_실질수수료율
    else:
        if dg: dg['실질수수료율']=dg.get('진짜수수료율',0)

    def pf_contrib(d):
        if not d or d['총매출']<=0: return 0.0
        return 1 - d['진짜수수료율'] - 변동비율

    pc="#0F6E56" if final>=0 else "#dc2626"
    dk="#085041" if final>=0 else "#991b1b"
    st.markdown(f"""
    <div class="result-card" style="background:linear-gradient(135deg,{pc},{dk})">
        <div class="label">이번 달 최종 순이익</div>
        <div class="value">{final:+,.0f}원</div>
        <div class="sub">영업이익률 {margin:.1f}%</div>
    </div>""",unsafe_allow_html=True)

    m1,m2,m3=st.columns(3)
    with m1: st.metric("배달 주문건수",f"{total_orders:,}건" if total_orders else "—")
    with m2: st.metric("배달 객단가",f"{avg_price:,.0f}원" if avg_price else "—")
    with m3: st.metric("총 매출",f"{total_gross:,.0f}원" if total_gross else "—")

    if any([bd,cp,yg,dg,nv]):
        st.divider()
        st.markdown("**플랫폼별 수수료율**")
        pf_info=[("배민",bd,"#1D9E75"),("쿠팡",cp,"#f97316"),
                 ("요기요",yg,"#dc2626"),("땡겨요",dg,"#7c3aed"),("네이버",nv,"#059669")]
        cols=st.columns(5)
        for i,(name,d,color) in enumerate(pf_info):
            with cols[i]:
                if d and d['총매출']>0:
                    # 땡겨요는 실질 수수료율(배달대행비 포함) 표시
                    if name=="땡겨요" and d.get('실질수수료율'):
                        fr=d['실질수수료율']*100
                        fr_sub="(배달대행비 포함)"
                    else:
                        fr=d['진짜수수료율']*100
                        fr_sub=""
                    cmp_html=""
                    if prev_data:
                        prev_fr=prev_data.get(f'{name}수수료율',None)
                        if prev_fr is not None:
                            diff=fr-float(prev_fr)
                            if abs(diff)>=0.1:
                                cls="fc-cmp badge-warn" if diff>0 else "fc-cmp badge-ok"
                                arrow="▲" if diff>0 else "▼"
                                cmp_html=f'<span class="{cls}">{arrow}{abs(diff):.1f}%p</span>'
                    st.markdown(f"""
                    <div class="fee-card">
                        <div class="fc-label">{name}</div>
                        <div class="fc-pct" style="color:{color};">{fr:.1f}%</div>
                        <div class="fc-amt">{d['총매출']-d['순이익']:,.0f}원</div>
                        {f'<div style="font-size:.7rem;color:#888;">{fr_sub}</div>' if fr_sub else ''}
                        {cmp_html}
                    </div>""",unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="fee-card"><div class="fc-label">{name}</div><div class="fc-pct" style="color:#ccc;">—</div></div>',unsafe_allow_html=True)

        if total_platform_fee>0 and delivery_gross>0:
            delivery_fee_pct=(total_platform_fee-pos_card_fee)/delivery_gross*100 if delivery_gross>0 else 0
            st.markdown(f"""
            <div style="background:#FEF3C7;border-radius:8px;padding:.7rem 1rem;margin-top:.6rem;font-size:.88rem;color:#78350f;">
            💰 이번 달 플랫폼 총 수수료: <strong>{total_platform_fee:,.0f}원</strong>
            &nbsp;(배달앱 매출의 {delivery_fee_pct:.1f}%)
            </div>""",unsafe_allow_html=True)

    if any([bd,cp,yg,dg,nv]):
        st.divider()
        tab1,tab2,tab3=st.tabs(["📊 매출 구성","📉 수수료 vs 실수령액","📦 플랫폼 객단가"])
        pf_chart=[("배민",bd,"#1D9E75"),("쿠팡",cp,"#f97316"),
                  ("요기요",yg,"#dc2626"),("땡겨요",dg,"#7c3aed"),("네이버",nv,"#059669")]
        if pos_sales>0:
            pf_chart.append(("오프라인",{'총매출':pos_sales,'순이익':pos_net,'주문건수':0,'객단가':0,'진짜수수료율':pos_card_fee/pos_sales},"#6b7280"))
        with tab1:
            lb=[n for n,d,c in pf_chart if d and d['총매출']>0]
            vl=[d['총매출'] for n,d,c in pf_chart if d and d['총매출']>0]
            cl=[c for n,d,c in pf_chart if d and d['총매출']>0]
            if lb:
                fig=go.Figure(go.Pie(labels=lb,values=vl,marker_colors=cl,hole=.4,textinfo='label+percent',textfont_size=12))
                fig.update_layout(showlegend=False,margin=dict(t=10,b=10,l=10,r=10),height=260)
                st.plotly_chart(fig,use_container_width=True)
        with tab2:
            bl=[n for n,d,c in pf_chart[:5] if d and d['총매출']>0]
            br=[d['순이익'] for n,d,c in pf_chart[:5] if d and d['총매출']>0]
            bf=[d['총매출']-d['순이익'] for n,d,c in pf_chart[:5] if d and d['총매출']>0]
            if bl:
                fig2=go.Figure()
                fig2.add_bar(name="실수령액",x=bl,y=br,marker_color="#1D9E75",
                             text=[f"{v/d['총매출']*100:.0f}%남음" for v,(n,d,c) in zip(br,[(n,d,c) for n,d,c in pf_chart[:5] if d and d['총매출']>0])],
                             textposition='inside',textfont_color='white')
                fig2.add_bar(name="수수료",x=bl,y=bf,marker_color="#dc2626",
                             text=[f"{v:,.0f}" for v in bf],textposition='inside',textfont_color='white')
                fig2.update_layout(barmode='stack',height=260,margin=dict(t=10,b=10,l=10,r=10),
                                   legend=dict(orientation='h',y=-0.2))
                st.plotly_chart(fig2,use_container_width=True)
        with tab3:
            po=[(n,d) for n,d,c in pf_chart[:5] if d and d.get('객단가',0)>0]
            if po:
                fig3=go.Figure(go.Bar(
                    x=[n for n,d in po],y=[d['객단가'] for n,d in po],
                    marker_color=[c for n,d,c in pf_chart[:5] if d and d.get('객단가',0)>0],
                    text=[f"{d['객단가']:,.0f}원" for n,d in po],textposition='outside'))
                max_val=max([d['객단가'] for n,d in po]) if po else 0
                fig3.update_layout(height=300,margin=dict(t=50,b=10,l=10,r=10),showlegend=False,
                                   yaxis_range=[0, max_val*1.25])
                st.plotly_chart(fig3,use_container_width=True)

    st.divider()
    target_profit=st.number_input("🎯 목표 순이익 (원) — 경영 지표에 반영됩니다",
                                   min_value=0,value=0,step=100000,format="%d")
    if target_profit>0:
        st.markdown(f'<div class="hangul-hint">→ {num_to_korean(target_profit)}</div>',unsafe_allow_html=True)

    if total_rev>0:

        # ✅ 원가구조 3줄 요약 카드
        st.markdown("**📊 이번 달 100원 팔면 구조**")
        prev_변동비율=float(prev_data.get('변동비율',0)) if prev_data else 0
        prev_전체수수료율=float(prev_data.get('총수수료',0))/float(prev_data.get('총매출',1)) if prev_data and prev_data.get('총매출',0)>0 else 0

        def delta_str(cur, prev):
            if prev==0: return ""
            diff=(cur-prev)*100
            if abs(diff)<0.1: return ""
            arrow="▲" if diff>0 else "▼"
            color="#dc2626" if diff>0 else "#0F6E56"
            return f'<span style="font-size:.72rem;color:{color};margin-left:4px;">{arrow}{abs(diff):.1f}%p</span>'

        fee_delta=delta_str(전체수수료율, prev_전체수수료율)
        var_delta=delta_str(변동비율, prev_변동비율)
        cm_delta=delta_str(-(공헌이익률), -(1-prev_전체수수료율-prev_변동비율)) if prev_data else ""

        # 배달앱만 수수료율 / 오프라인 따로 계산
        배달수수료율 = (delivery_gross - sum([x['순이익'] for x in [bd,cp,yg,dg,nv] if x])) / delivery_gross if delivery_gross > 0 else 0

        st.markdown(f"""
        <div class="detail-block" style="padding:1rem 1.4rem;">
          <div style="font-size:.8rem;color:#888;margin-bottom:.8rem;">
            💡 100원 팔면 수수료·재료비 빠지고 <b>{공헌이익률*100:.1f}%({공헌이익률*100:.1f}원)</b>이 남아요. 그 돈으로 월세·인건비를 내는 거예요.
          </div>

          <div style="display:flex;justify-content:space-between;align-items:center;padding:.4rem 0;border-bottom:1px solid rgba(128,128,128,.1);">
            <span style="font-size:.88rem;">🏪 전체 수수료율
              <span style="font-size:.72rem;color:#888;">(배달앱+카드수수료 합산)</span>
            </span>
            <span style="font-weight:700;color:#dc2626;">{전체수수료율*100:.1f}% ({전체수수료율*100:.1f}원){fee_delta}</span>
          </div>

          <div style="padding:.3rem 0 .4rem 1rem;border-bottom:1px solid rgba(128,128,128,.1);">
            <div style="display:flex;justify-content:space-between;font-size:.8rem;color:#888;padding:.15rem 0;">
              <span>└ 배달앱만 <span style="font-size:.7rem;">(배달매출 기준)</span></span>
              <span style="color:#dc2626;font-weight:600;">{배달수수료율*100:.1f}%</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:.8rem;color:#888;padding:.15rem 0;">
              <span>└ 오프라인 카드수수료</span>
              <span style="color:#888;font-weight:600;">1.1%</span>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;align-items:center;padding:.4rem 0;border-bottom:1px solid rgba(128,128,128,.1);">
            <span style="font-size:.88rem;">🥚 재료비율(변동비율)
              <span style="font-size:.72rem;color:#888;">(재료비+배달대행비+광고비 등)</span>
            </span>
            <span style="font-weight:700;color:#f97316;">{변동비율*100:.1f}% ({변동비율*100:.1f}원){var_delta}</span>
          </div>

          <div style="display:flex;justify-content:space-between;align-items:center;padding:.4rem 0;">
            <span style="font-size:.88rem;font-weight:700;">💰 내 손에 남는 돈
              <span style="font-size:.72rem;color:#888;font-weight:400;">(고정비 내기 전)</span>
            </span>
            <span style="font-weight:700;color:#0F6E56;font-size:1.05rem;">{공헌이익률*100:.1f}% ({공헌이익률*100:.1f}원){cm_delta}</span>
          </div>

          <div style="margin-top:.6rem;padding:.5rem .8rem;background:rgba(15,110,86,.07);border-radius:6px;font-size:.78rem;color:#555;">
            📌 전체 수수료율이 낮아 보이는 이유: 수수료가 낮은 오프라인 매출({pos_sales/total_gross*100:.0f}%)이 포함됐기 때문이에요.
            배달앱만 따지면 실제 수수료율은 <b>{배달수수료율*100:.1f}%</b>예요.
          </div>
        </div>""", unsafe_allow_html=True)

        # 변동비율 이상 감지
        if prev_변동비율>0:
            변동비차이=(변동비율-prev_변동비율)*100
            if 변동비차이>=3:
                st.markdown(f'<div class="insight-box">🚨 재료비율이 전월보다 {변동비차이:.1f}%p 올랐어요! 재료비·배달대행비 항목 확인이 필요해요.</div>',unsafe_allow_html=True)
            elif 변동비차이>=1:
                st.markdown(f'<div class="insight-box">⚠️ 재료비율이 전월보다 {변동비차이:.1f}%p 올랐어요. 원인을 확인해보세요.</div>',unsafe_allow_html=True)
            elif 변동비차이<=-1:
                st.markdown(f'<div class="insight-box insight-good">✅ 재료비율이 전월보다 {abs(변동비차이):.1f}%p 내렸어요! 재료 관리가 잘 되고 있어요.</div>',unsafe_allow_html=True)

        st.markdown("**📐 경영 지표**")
        sim1,sim2,sim3=st.columns(3)

        # 손익분기점 달력 계산
        if bep>0 and total_gross>0:
            import calendar
            days_in_month=30
            bep_day=int(bep/total_gross*days_in_month)+1
            bep_day=min(bep_day,days_in_month)
        else:
            bep_day=0

        bep_gap=total_rev-bep
        bep_color="#0F6E56" if bep_gap>=0 else "#dc2626"

        with sim1:
            if 공헌이익률<=0:
                st.markdown("""
                <div class="kpi-card">
                    <div class="kc-label">손익분기점</div>
                    <div class="kc-value" style="color:#dc2626;">계산 불가</div>
                    <div class="kc-sub">⚠️ 재료비+수수료가 너무 높아요<br>변동비 항목을 확인해주세요</div>
                </div>""",unsafe_allow_html=True)
            else:
                bep_sub2=f"✅ 이번 달 달성! ({abs(bep_gap)/10000:.0f}만원 초과)" if bep_gap>=0 else f"⚠️ {abs(bep_gap)/10000:.0f}만원 더 팔아야 해요"
                calendar_msg=f"📅 매달 {bep_day}일까지는 고정비 내는 기간,<br>{bep_day+1}일부터 진짜 내 돈!" if bep_day>0 else ""
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kc-label">손익분기점 <span style="font-size:.68rem;color:#aaa;">(이 금액 팔아야 순이익 0원)</span></div>
                    <div class="kc-value" style="color:{bep_color};">{bep/10000:.0f}만원</div>
                    <div class="kc-sub">{bep_sub2}<br>{calendar_msg}</div>
                </div>""",unsafe_allow_html=True)
        with sim2:
            if target_profit>0 and 공헌이익률>0:
                부족액=max(0,target_profit-final)
                if 부족액==0:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kc-label">목표 달성</div>
                        <div class="kc-value" style="color:#0F6E56;">✅ 달성!</div>
                        <div class="kc-sub">목표 {target_profit:,.0f}원 초과 달성</div>
                    </div>""",unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="kpi-card">
                        <div class="kc-label">목표까지 부족액</div>
                        <div class="kc-value" style="color:#7c3aed;">{부족액:,.0f}원</div>
                        <div class="kc-sub">목표 {target_profit:,.0f}원 / 현재 {final:,.0f}원</div>
                    </div>""",unsafe_allow_html=True)
            else:
                st.markdown("""<div class="kpi-card">
                    <div class="kc-label">목표 달성 분석</div>
                    <div class="kc-value" style="color:#ccc;font-size:.95rem;">목표 순이익 입력 후 확인</div>
                </div>""",unsafe_allow_html=True)
        with sim3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kc-label">100원 팔면 남는 돈
                  <span style="font-size:.68rem;color:#aaa;"> (수수료·재료비 빼고)</span>
                </div>
                <div class="kc-value" style="color:#f97316;">{공헌이익률*100:.1f}%</div>
                <div class="kc-sub">
                  100원 팔면 <b>{공헌이익률*100:.1f}원</b> 남음<br>
                  이 돈으로 월세·인건비 내는 거예요<br>
                  <span style="color:#888;">(고정비 빼기 전 기준)</span>
                </div>
            </div>""",unsafe_allow_html=True)

        all_target_pfs=[
            ("배민",bd,"#1D9E75"),("쿠팡",cp,"#f97316"),("요기요",yg,"#dc2626"),
            ("땡겨요",dg,"#7c3aed"),("네이버",nv,"#059669"),
            ("오프라인",{'순이익':pos_net,'총매출':pos_sales,'진짜수수료율':pos_card_fee/pos_sales if pos_sales>0 else 0} if pos_sales>0 else None,"#6b7280"),
        ]
        if target_profit>0 and final<target_profit:
            부족액=target_profit-final
            st.markdown("**🎯 목표 달성 — 채널별 추가 매출**")
            st.caption(f"현재 순이익 {final:,.0f}원 → 목표 {target_profit:,.0f}원 | 부족액 {부족액:,.0f}원")
            rows_html=""
            for name,d,color in all_target_pfs:
                if d and d.get('총매출',0)>0:
                    cr=1-d['진짜수수료율']-변동비율
                    if cr>0:
                        추가=부족액/cr
                        rows_html+=f'<div class="sim-row"><span style="color:{color};font-weight:500;">{name} <small style="color:#888;">100원 팔면 {cr*100:.1f}%({cr*100:.1f}원) 남음</small></span><span class="pos">+{추가:,.0f}원 더 팔아야</span></div>'
            st.markdown(f'<div class="detail-block">{rows_html}</div>',unsafe_allow_html=True)

    if any([bd,cp,yg,dg,nv]) and 변동비율>0:
        st.divider()
        st.markdown("**📊 객단가 시뮬레이션**")
        st.caption("이미 출발한 배달에 메뉴 추가 시 → 배달비 고정, 추가분만 이익 계산")
        sim_amount=st.number_input("객단가 추가 금액 (원)",min_value=0,value=1000,step=500,format="%d",key="sim_amt")
        if sim_amount>0:
            rows_html=""
            all_pfs=[("배민",bd,"#1D9E75",baemin_orders),("쿠팡",cp,"#f97316",cp['주문건수'] if cp else 0),
                     ("요기요",yg,"#dc2626",yg['주문건수'] if yg else 0),("땡겨요",dg,"#7c3aed",dg['주문건수'] if dg else 0)]
            for name,d,color,건수 in all_pfs:
                if d and 건수>0:
                    cr=pf_contrib(d)
                    추가=건수*sim_amount*cr
                    rows_html+=f'<div class="sim-row"><span style="color:{color};">{name} {건수}건</span><span class="pos">약 +{추가:,.0f}원</span></div>'
            if rows_html:
                st.markdown(f'<div class="detail-block">{rows_html}</div>',unsafe_allow_html=True)
            if not baemin_orders and bd:
                st.caption("📦 배달의민족 건수를 입력하면 배민도 포함됩니다.")

    if show_prev and prev_data:
        st.divider()
        st.markdown("**📅 전월 대비**")
        cols_prev=st.columns(4)
        items=[("최종 순이익",final,prev_data.get('최종순이익',0),False),
               ("플랫폼 실수령액",platform_sum,prev_data.get('플랫폼실수령액',0),False),
               ("총 수수료",total_platform_fee,prev_data.get('총수수료',0),True),
               ("배달 객단가",avg_price,prev_data.get('평균객단가',0),False)]
        for i,(label,cur,prv,inv) in enumerate(items):
            with cols_prev[i]:
                diff=cur-float(prv)
                st.metric(label,f"{cur:,.0f}원",delta=f"{diff:+,.0f}원",delta_color="inverse" if inv else "normal")
        prev_변동비율=float(prev_data.get('변동비율',0))
        if prev_변동비율>0 and 변동비율>0:
            변동비차이=(변동비율-prev_변동비율)*100
            if abs(변동비차이)>=1.0:
                icon="⚠️" if 변동비차이>0 else "✅"
                msg=f"재료비·물류비 등 변동비율이 전월 대비 {abs(변동비차이):.1f}%p {'올랐어요' if 변동비차이>0 else '내렸어요'}. (전월 {prev_변동비율*100:.1f}% → 이번달 {변동비율*100:.1f}%)"
                css="insight-box" if 변동비차이>0 else "insight-box insight-good"
                st.markdown(f'<div class="{css}">{icon} {msg}</div>',unsafe_allow_html=True)

    st.divider()

    if bd:
        baemin_orders=st.number_input("📦 배달의민족 주문건수 (사장님앱 확인 후 입력)",
                                       min_value=0,value=st.session_state.get("baemin_orders",0),
                                       step=1,format="%d",key="baemin_orders",
                                       help="배민 파일은 일별 합산이라 자동계산 불가")
        bd['주문건수']=baemin_orders
        bd['객단가']=bd['총매출']/baemin_orders if baemin_orders>0 else 0
        bd_n=baemin_orders if baemin_orders>0 else None
        bd_m=bd['총매출'] if bd['총매출']>0 else 1
        rows=(detail_row("총 매출 (음식값)",bd['총매출'])+
              detail_row("└ 바로결제",bd['총매출']-bd['G만나서식대'],sub=True)+
              (detail_row("└ 만나서결제 식대",bd['G만나서식대'],sub=True) if bd['G만나서식대'] else "")+
              (detail_row("└ 만나서결제 배달팁",bd['O만나서배달팁'],sub=True) if bd['O만나서배달팁'] else "")+
              detail_row("중개 수수료",bd['중개수수료'],per_unit=abs(bd['중개수수료'])/bd_n if bd_n else None,pct=abs(bd['중개수수료'])/bd_m*100)+
              detail_row("결제 수수료",bd['결제수수료'],per_unit=abs(bd['결제수수료'])/bd_n if bd_n else None,pct=abs(bd['결제수수료'])/bd_m*100)+
              detail_row("배달비",bd['배달비'],per_unit=abs(bd['배달비'])/bd_n if bd_n else None)+
              detail_row("광고비",bd['광고비'],per_unit=abs(bd['광고비'])/bd_n if bd_n else None,pct=abs(bd['광고비'])/bd_m*100)+
              (detail_row("즉시할인",bd['즉시할인'],per_unit=abs(bd['즉시할인'])/bd_n if bd_n else None,pct=abs(bd['즉시할인'])/bd_m*100) if bd['즉시할인'] else "")+
              detail_row("부가세",bd['부가세'],per_unit=abs(bd['부가세'])/bd_n if bd_n else None,pct=abs(bd['부가세'])/bd_m*100)+
              detail_row("배민 실수령액",bd['순이익'],total=True))
        ord_txt=f"{baemin_orders}건" if baemin_orders>0 else "건수 입력필요"
        avg_b=f'<span class="badge badge-green">객단가 {bd["객단가"]:,.0f}원</span>' if baemin_orders>0 else ""
        st.markdown(f'<div class="detail-block"><div class="detail-title">🟢 배달의민족 <span class="badge badge-green">{ord_txt}</span>{avg_b}</div>{rows}</div>',unsafe_allow_html=True)

    if cp:
        cp_유료=cp['주문건수']-cp['배달비_무료건수']
        n=cp['주문건수'] if cp['주문건수']>0 else 1; m=cp['총매출'] if cp['총매출']>0 else 1
        rows=(detail_row("총 매출",cp['총매출'])+
              detail_row("중개 이용료",-cp['중개수수료'],per_unit=cp['중개수수료']/n,pct=cp['중개수수료']/m*100)+
              detail_row("결제대행사 수수료",-cp['결제수수료'],per_unit=cp['결제수수료']/n,pct=3.0)+
              detail_row("배달비",-cp['배달비'],per_unit=3400 if cp_유료>0 else 0)+
              detail_row("광고비",-cp['광고비'],per_unit=cp['광고비']/n,pct=cp['광고비']/m*100)+
              (detail_row("상점부담 쿠폰",-cp['상점쿠폰'],per_unit=cp['상점쿠폰']/n,pct=cp['상점쿠폰']/m*100) if cp['상점쿠폰'] else "")+
              (detail_row("즉시할인",-cp['즉시할인'],per_unit=cp['즉시할인']/n,pct=cp['즉시할인']/m*100) if cp['즉시할인'] else "")+
              detail_row("쿠팡이츠 실수령액",cp['순이익'],total=True))
        st.markdown(f'<div class="detail-block"><div class="detail-title">🟠 쿠팡이츠 <span class="badge badge-amber">{cp["주문건수"]}건</span><span class="badge badge-amber">객단가 {cp["객단가"]:,.0f}원</span></div>{rows}</div>',unsafe_allow_html=True)

    if yg:
        n=yg['주문건수'] if yg['주문건수']>0 else 1; m=yg['총매출'] if yg['총매출']>0 else 1
        rows=(detail_row("총 매출",yg['총매출'])+
              (detail_row("요타임딜 할인",-yg['타임딜할인'],per_unit=yg['타임딜할인']/n,pct=yg['타임딜할인']/m*100) if yg['타임딜할인'] else "")+
              (detail_row("쿠폰 할인",-yg['쿠폰할인'],per_unit=yg['쿠폰할인']/n,pct=yg['쿠폰할인']/m*100) if yg['쿠폰할인'] else "")+
              detail_row("중개 이용료",-yg['중개이용료'],per_unit=yg['중개이용료']/n,pct=yg['중개이용료']/m*100)+
              detail_row("결제 이용료",-yg['결제이용료'],per_unit=yg['결제이용료']/n,pct=yg['결제이용료']/m*100)+
              detail_row("배달대행 이용료",-yg['배달대행이용료'],per_unit=yg['배달대행이용료']/n)+
              (detail_row("요타임딜 이용료",-yg['타임딜이용료'],per_unit=yg['타임딜이용료']/n,pct=yg['타임딜이용료']/m*100) if yg['타임딜이용료'] else "")+
              (detail_row("광고비",-yg['광고비'],per_unit=yg['광고비']/n,pct=yg['광고비']/m*100) if yg['광고비'] else "")+
              detail_row("요기요 실수령액",yg['순이익'],total=True))
        st.markdown(f'<div class="detail-block"><div class="detail-title">🔴 요기요 <span class="badge badge-coral">{yg["주문건수"]}건</span><span class="badge badge-coral">객단가 {yg["객단가"]:,.0f}원</span></div>{rows}</div>',unsafe_allow_html=True)

    if dg:
        n=dg['주문건수'] if dg['주문건수']>0 else 1; m=dg['총매출'] if dg['총매출']>0 else 1
        실제손에쥔돈=dg['순이익']-dg['배달대행이용료']
        rows=(detail_row("총 매출",dg['총매출'])+
              detail_row("주문중개 이용료",-dg['중개이용료'],per_unit=dg['중개이용료']/n,pct=dg['중개이용료']/m*100)+
              detail_row("결제정산 이용료",-dg['결제정산이용료'],per_unit=dg['결제정산이용료']/n,pct=dg['결제정산이용료']/m*100)+
              (detail_row("사장님 쿠폰",-dg['사장님쿠폰'],per_unit=dg['사장님쿠폰']/n) if dg['사장님쿠폰'] else "")+
              detail_row("땡겨요 실수령액",dg['순이익'],total=True)+
              (f'<div class="detail-row" style="align-items:flex-start;"><span style="color:#dc2626;">배달대행비 (별도지불)</span><div style="text-align:right;"><div class="neg">-{dg["배달대행이용료"]:,.0f}원</div><div style="font-size:.75rem;color:#888;">건당 {dg["배달대행이용료"]/n:,.0f}원</div></div></div>' if dg['배달대행이용료']>0 else "")+
              (f'<div class="detail-row total"><span>실제 손에 쥔 돈</span><span class="pos">+{실제손에쥔돈:,.0f}원</span></div>' if dg['배달대행이용료']>0 else "")+
              f'<div class="detail-row sub"><span>※ 배달대행비는 ⑤변동비에 포함됨 (이중차감 없음)</span><span></span></div>')
        st.markdown(f'<div class="detail-block"><div class="detail-title">🟣 땡겨요 <span class="badge badge-purple">{dg["주문건수"]}건</span><span class="badge badge-purple">객단가 {dg["객단가"]:,.0f}원</span></div>{rows}</div>',unsafe_allow_html=True)

    if nv:
        n=nv['주문건수'] if nv['주문건수']>0 else 1; m=nv['총매출'] if nv['총매출']>0 else 1
        rows=(detail_row("총 매출",nv['총매출'])+
              (detail_row("취소 환불",nv['취소매출']) if nv.get('취소매출') else "")+
              detail_row("Npay 수수료",nv['Npay수수료'],per_unit=abs(nv['Npay수수료'])/n,pct=abs(nv['Npay수수료'])/m*100 if m else 0)+
              detail_row("네이버 실수령액",nv['순이익'],total=True))
        st.markdown(f'<div class="detail-block"><div class="detail-title">🟢 네이버 <span class="badge badge-blue">{nv["주문건수"]}건</span><span class="badge badge-blue">객단가 {nv["객단가"]:,.0f}원</span></div>{rows}</div>',unsafe_allow_html=True)

    if pos_sales>0:
        rows=(detail_row("포스기 매출",pos_sales)+
              detail_row("카드수수료 (1.1%)",-pos_card_fee)+
              detail_row("오프라인 실수령액",pos_net,total=True))
        st.markdown(f'<div class="detail-block"><div class="detail-title">🏪 오프라인</div>{rows}</div>',unsafe_allow_html=True)

    # ✅ 고정비 상세 (4대보험 포함)
    fixed_items=[("월세",rent),("관리비",manage),("인건비 (세전)",labor),
                 ("4대보험 회사부담 (×10.5%)",insurance),
                 ("기장료",jangryeo),("포스기 유지비",pos_maint)]
    if fixed_total>0:
        rows="".join([detail_row(n,-v) for n,v in fixed_items if v>0])
        rows+=detail_row("고정비 합계",-fixed_total,total=True)
        st.markdown(f'<div class="detail-block"><div class="detail-title">🔒 고정비 (4대보험 포함)</div>{rows}</div>',unsafe_allow_html=True)

    var_items=[("동원 물류비",dongwon),("만월상회 (음료원액)",manwol),("계란",eggs),
               ("포장박스",boxes),("배달대행비",delivery_agency),
               ("소모품 카드결제",consumables),("기타 카드수수료",card_fee_etc),("광고비",ad_cost)]
    if var_total>0:
        rows="".join([detail_row(n,-v) for n,v in var_items if v>0])
        rows+=detail_row("변동비 합계",-var_total,total=True)
        st.markdown(f'<div class="detail-block"><div class="detail-title">📦 변동비</div>{rows}</div>',unsafe_allow_html=True)

    if cp and cp.get('시간대') and len(cp['시간대'])>0:
        st.divider()
        st.markdown("**⏰ 주문 시간대 분석 (쿠팡이츠 기준)**")
        tab_h1,tab_h2=st.tabs(["시간대별","요일×시간 히트맵"])
        weekday_names=["월","화","수","목","금","토","일"]
        with tab_h1:
            시간대=cp['시간대']
            hours=sorted(시간대.keys())
            counts=[시간대[h] for h in hours]
            labels=[f"{h:02d}시" for h in hours]
            peak_h=max(시간대,key=시간대.get)
            max_cnt=max(counts) if counts else 1
            fig_h=go.Figure(go.Bar(x=labels,y=counts,
                marker_color=["#dc2626" if h==peak_h else "#f97316" for h in hours],
                text=counts,textposition='outside'))
            fig_h.update_layout(height=280,margin=dict(t=50,b=10,l=10,r=10),
                               showlegend=False,yaxis_range=[0,max_cnt*1.3])
            st.plotly_chart(fig_h,use_container_width=True)
            st.caption(f"🔴 피크타임: {peak_h:02d}시 ({시간대[peak_h]}건)")
        with tab_h2:
            히트맵=cp['히트맵']
            if 히트맵:
                all_hours=sorted(set(h for row in 히트맵.values() for h in row.keys()))
                z=[]; y_labels=[]
                for wd in range(7):
                    row_data=히트맵.get(wd,{})
                    if any(row_data.get(h,0)>0 for h in all_hours):
                        z.append([row_data.get(h,0) for h in all_hours])
                        y_labels.append(weekday_names[wd])
                if z:
                    fig_hm=go.Figure(go.Heatmap(
                        z=z,x=[f"{h:02d}시" for h in all_hours],y=y_labels,
                        colorscale=[[0,"#fff7ed"],[0.4,"#f97316"],[1,"#dc2626"]],
                        text=[[str(v) if v>0 else "" for v in row] for row in z],
                        texttemplate="%{text}",textfont={"size":11},showscale=True))
                    fig_hm.update_layout(height=280,margin=dict(t=10,b=10,l=40,r=10))
                    st.plotly_chart(fig_hm,use_container_width=True)
                    peak_wd,peak_h,peak_cnt=0,0,0
                    for wd,hrs in 히트맵.items():
                        for h,cnt in hrs.items():
                            if cnt>peak_cnt: peak_wd,peak_h,peak_cnt=wd,h,cnt
                    st.caption(f"🔴 최다 주문: {weekday_names[peak_wd]}요일 {peak_h:02d}시 ({peak_cnt}건)")

    if monthly_files_left and len(monthly_files_left)>=1:
        monthly_data=[]
        for f in monthly_files_left:
            try:
                df_m=pd.read_excel(f,sheet_name='비교데이터',index_col=0)
                d=df_m.to_dict()['값']
                # 변동비 세부 항목 읽기
                var_items_data={}
                for item_name in ['동원 물류비','만월상회 (음료원액)','계란','포장박스','배달대행비','소모품 카드결제','기타 카드수수료','광고비']:
                    key=f'변동비_{item_name}'
                    var_items_data[item_name]=float(d.get(key,0))
                # 플랫폼별 매출
                plat_sales={}
                for p in ['배민','쿠팡','요기요','땡겨요','네이버']:
                    plat_sales[p]=float(d.get(f'{p}매출',0))
                plat_sales['포스기']=float(d.get('포스기매출',0))

                monthly_data.append({
                    '월':str(d.get('분析월','')),
                    '순이익':float(d.get('최종순이익',0)),
                    '수수료':float(d.get('총수수료',0)),
                    '변동비율':float(d.get('변동비율',0))*100,
                    '총매출':float(d.get('총매출',0)),
                    '영업이익률':float(d.get('영업이익률',0)),
                    '평균객단가':float(d.get('평균객단가',0)),
                    '변동비_세부':var_items_data,
                    '플랫폼매출':plat_sales,
                })
            except: pass
        if len(monthly_data)>=2:
            st.divider()
            st.markdown("**📈 월별 추이**")
            monthly_data.sort(key=lambda x: x['월'])
            months=[d['월'] for d in monthly_data]

            tab_m1,tab_m2,tab_m3,tab_m4,tab_m5,tab_m6,tab_m7=st.tabs([
                "순이익","총매출","영업이익률","수수료","변동비율","객단가","변동비 세부"
            ])

            def line_chart(y_vals, color, fmt_fn, height=230):
                fig=go.Figure(go.Scatter(
                    x=months, y=y_vals, mode='lines+markers+text',
                    line=dict(color=color,width=2), marker=dict(size=8),
                    text=[fmt_fn(v) for v in y_vals], textposition='top center'))
                fig.update_layout(height=height,margin=dict(t=30,b=10,l=10,r=10),showlegend=False)
                return fig

            def bar_chart(y_vals, color, fmt_fn, height=230):
                fig=go.Figure(go.Bar(
                    x=months, y=y_vals, marker_color=color,
                    text=[fmt_fn(v) for v in y_vals], textposition='outside'))
                fig.update_layout(height=height,margin=dict(t=30,b=10,l=10,r=10),showlegend=False)
                return fig

            with tab_m1:
                st.plotly_chart(line_chart(
                    [d['순이익'] for d in monthly_data],'#0F6E56',
                    lambda v:f"{v/10000:.0f}만"), use_container_width=True)

            with tab_m2:
                st.plotly_chart(bar_chart(
                    [d['총매출'] for d in monthly_data],'#3b82f6',
                    lambda v:f"{v/10000:.0f}만"), use_container_width=True)

            with tab_m3:
                st.plotly_chart(line_chart(
                    [d['영업이익률'] for d in monthly_data],'#7c3aed',
                    lambda v:f"{v:.1f}%"), use_container_width=True)

            with tab_m4:
                st.plotly_chart(bar_chart(
                    [d['수수료'] for d in monthly_data],'#dc2626',
                    lambda v:f"{v/10000:.0f}만"), use_container_width=True)

            with tab_m5:
                st.plotly_chart(line_chart(
                    [d['변동비율'] for d in monthly_data],'#f97316',
                    lambda v:f"{v:.1f}%"), use_container_width=True)

            with tab_m6:
                st.plotly_chart(bar_chart(
                    [d['평균객단가'] for d in monthly_data],'#059669',
                    lambda v:f"{v:,.0f}원"), use_container_width=True)

            with tab_m7:
                # 변동비 항목별 막대 그래프
                item_colors={
                    '동원 물류비':'#1D9E75','만월상회 (음료원액)':'#f97316',
                    '계란':'#fbbf24','포장박스':'#6b7280',
                    '배달대행비':'#dc2626','소모품 카드결제':'#7c3aed',
                    '기타 카드수수료':'#0ea5e9','광고비':'#ec4899'
                }
                fig_var=go.Figure()
                for item_name, color in item_colors.items():
                    vals=[d['변동비_세부'].get(item_name,0) for d in monthly_data]
                    if any(v>0 for v in vals):
                        fig_var.add_trace(go.Bar(
                            name=item_name, x=months, y=vals,
                            marker_color=color,
                            text=[f"{v/10000:.1f}만" if v>0 else "" for v in vals],
                            textposition='outside'
                        ))
                fig_var.update_layout(
                    barmode='group', height=320,
                    margin=dict(t=20,b=10,l=10,r=10),
                    legend=dict(orientation='h',y=-0.25,font_size=11))
                st.plotly_chart(fig_var,use_container_width=True)
                st.caption("💡 항목별 지출을 월별로 비교해보세요. 갑자기 오른 항목이 있으면 원인을 확인해보세요!")

            # 플랫폼별 매출 비중 추이 (포스기 포함)
            st.markdown("**📊 플랫폼별 매출 비중 추이**")
            pf_colors_trend={
                '배민':'#1D9E75','쿠팡':'#f97316','요기요':'#dc2626',
                '땡겨요':'#7c3aed','네이버':'#059669','포스기':'#6b7280'
            }
            fig_pf=go.Figure()
            for pf, color in pf_colors_trend.items():
                vals=[d['플랫폼매출'].get(pf,0) for d in monthly_data]
                if any(v>0 for v in vals):
                    fig_pf.add_trace(go.Bar(
                        name=pf, x=months, y=vals,
                        marker_color=color,
                        text=[f"{v/10000:.0f}만" if v>0 else "" for v in vals],
                        textposition='inside', textfont_color='white'
                    ))
            fig_pf.update_layout(
                barmode='stack', height=300,
                margin=dict(t=10,b=10,l=10,r=10),
                legend=dict(orientation='h',y=-0.2,font_size=11))
            st.plotly_chart(fig_pf,use_container_width=True)
            st.caption("💡 배달앱과 오프라인 비중 변화를 확인해보세요. 수수료 낮은 채널 비중이 늘수록 유리해요!")


    st.divider()
    if total_rev>0 or total_gross>0:
        pdf_data={
            'month_str':data_month_str,'total_gross':total_gross,
            'total_platform_fee':total_platform_fee,'delivery_gross':delivery_gross,
            'platform_sum':platform_sum,'pos_sales':pos_sales,'pos_card_fee':pos_card_fee,
            'fixed_total':fixed_total,'var_total':var_total,
            'final':final,'margin':margin,'bep':bep,
            'total_orders':total_orders,'avg_price':avg_price,'변동비율':변동비율,
            'platforms':{'배민':bd,'쿠팡':cp,'요기요':yg,'땡겨요':dg,'네이버':nv},
            'fixed_items':fixed_items,'var_items':var_items,
        }
        today_str=datetime.date.today().strftime('%Y%m')
        dc1,dc2=st.columns(2)
        with dc1:
            try:
                excel_bytes=generate_excel(pdf_data)
                st.download_button(
                    label="📊 결과 엑셀 다운로드 (.xlsx)",data=excel_bytes,
                    file_name=f"진심카스테라_수익분석_{today_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,help="다음 달 전월 비교에 활용하세요")
            except Exception as e: st.warning(f"엑셀 생성 오류: {e}")
        with dc2:
            if REPORTLAB_OK:
                try:
                    pdf_bytes=generate_pdf(pdf_data)
                    st.download_button(
                        label="📄 리포트 PDF 다운로드",data=pdf_bytes,
                        file_name=f"진심카스테라_수익분석_{today_str}.pdf",
                        mime="application/pdf",use_container_width=True)
                except Exception as e: st.warning(f"PDF 생성 오류: {e}")
            else:
                st.info("PDF: `pip install reportlab` 설치 후 사용 가능")

st.divider()
st.caption("수식: 배민 SUM(AE)+SUM(G)+SUM(O) | 쿠팡 SUM(AN) | 요기요 직접계산 | 땡겨요 정산요약(E) | 네이버 SUM(L예약)+SUM(P) | 수수료율 역산(총매출-실수령액) | Gemini 교차검증 완료")
