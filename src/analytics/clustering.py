# src/analytics/clustering.py
import sqlite3, pandas as pd, numpy as np, logging
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from pathlib import Path

logger = logging.getLogger(__name__)

N_CLUSTERS = 5
FEATURES = ['return_on_equity_pct','debt_to_equity','revenue_cagr_5yr',
            'fcf_pct_sales','operating_profit_margin_pct']


def load_features(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("""
        SELECT r.company_id, r.return_on_equity_pct, r.debt_to_equity,
               r.revenue_cagr_5yr, r.free_cash_flow_cr,
               r.operating_profit_margin_pct, pl.sales
        FROM financial_ratios r
        JOIN profitandloss pl USING (company_id, year)
        WHERE r.year=(SELECT MAX(year) FROM financial_ratios WHERE company_id=r.company_id)
          AND pl.year=(SELECT MAX(year) FROM profitandloss WHERE company_id=pl.company_id)
    """, conn); conn.close()

    # Scale FCF by sales -> comparable % metric
    df['fcf_pct_sales'] = df['free_cash_flow_cr'] / df['sales'].replace(0,float('nan')) * 100

    # Winsorise P5/P95 + fill median
    for col in FEATURES:
        lo,hi = df[col].quantile(0.05), df[col].quantile(0.95)
        df[col] = df[col].clip(lo,hi).fillna(df[col].median())
    return df


def elbow_plot(X_scaled, output_dir, max_k=10):
    inertias, silhouettes = [], []
    for k in range(2, max_k+1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        lbl = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, lbl))

    fig,(ax1,ax2) = plt.subplots(1,2,figsize=(11/2.54,4.5/2.54))
    fig.patch.set_facecolor('#F8F7FF')
    ax1.plot(range(2,max_k+1), inertias, 'o-', color='#1B2A4A')
    ax1.axvline(N_CLUSTERS, color='#C9923A', linestyle='--', linewidth=1)
    ax1.set_title('Elbow - Inertia', fontsize=8); ax1.tick_params(labelsize=7)
    ax2.plot(range(2,max_k+1), silhouettes, 'o-', color='#0F766E')
    ax2.axvline(N_CLUSTERS, color='#C9923A', linestyle='--', linewidth=1)
    ax2.set_title('Silhouette Score', fontsize=8); ax2.tick_params(labelsize=7)
    plt.tight_layout()
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    fig.savefig(f'{output_dir}/elbow_plot.png', dpi=130, bbox_inches='tight')
    plt.close(fig)


def name_cluster(centroid):
    roe = centroid.get('return_on_equity_pct',0)
    de = centroid.get('debt_to_equity',0)
    cg = centroid.get('revenue_cagr_5yr',0)
    opm = centroid.get('operating_profit_margin_pct',0)
    fcf = centroid.get('fcf_pct_sales',0)
    if roe>20 and de<0.5: return 'High-Quality Compounders'
    if cg>15 and de<1: return 'Growth Leaders'
    if de>2: return 'Leveraged Cyclicals'
    if opm>20 and fcf>5: return 'Profitable Cash Generators'
    return 'Defensive Dividend Payers'


def run_clustering(db_path, output_dir='output'):
    df = load_features(db_path)
    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    elbow_plot(X_scaled, output_dir)

    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    df['cluster_id'] = km.fit_predict(X_scaled)

    # Centroid in original scale for labelling
    centroids_orig = scaler.inverse_transform(km.cluster_centers_)
    cdf = pd.DataFrame(centroids_orig, columns=FEATURES)
    name_map = {i: name_cluster(cdf.iloc[i].to_dict()) for i in range(N_CLUSTERS)}
    df['cluster_name'] = df['cluster_id'].map(name_map)

    df['distance_from_centroid'] = [
        np.linalg.norm(X_scaled[i] - km.cluster_centers_[df['cluster_id'].iloc[i]])
        for i in range(len(df))]

    result = df[['company_id','cluster_id','cluster_name','distance_from_centroid']]
    result.to_csv(f'{output_dir}/cluster_labels.csv', index=False)
    logger.info(f'Clustering: {N_CLUSTERS} clusters, {len(result)} companies')
    return result


def correlation_heatmap(db_path, output_dir='output'):
    COLS=['return_on_equity_pct','return_on_capital_pct','net_profit_margin_pct',
          'debt_to_equity','free_cash_flow_cr','revenue_cagr_5yr',
          'pat_cagr_5yr','asset_turnover','interest_coverage',
          'operating_profit_margin_pct']
    SHORT=['ROE','ROCE','NPM','D/E','FCF','RevCAGR5','PATCAGR5','AssetTO','ICR','OPM']

    conn = sqlite3.connect(db_path)
    df = pd.read_sql(f"SELECT {','.join(COLS)} FROM financial_ratios WHERE year=("
                      f"SELECT MAX(year) FROM financial_ratios WHERE company_id=financial_ratios.company_id)",
                      conn); conn.close()

    corr = df[COLS].corr(method='pearson')
    fig,ax = plt.subplots(figsize=(9/2.54,8.5/2.54))
    im = ax.imshow(corr.values, cmap='RdYlGn', vmin=-1, vmax=1)
    ax.set_xticks(range(len(SHORT))); ax.set_xticklabels(SHORT,rotation=45,ha='right',fontsize=6.5)
    ax.set_yticks(range(len(SHORT))); ax.set_yticklabels(SHORT,fontsize=6.5)
    for i in range(len(SHORT)):
        for j in range(len(SHORT)):
            ax.text(j,i,f'{corr.values[i,j]:.2f}',ha='center',va='center',
                     fontsize=5.5,color='black' if abs(corr.values[i,j])<0.7 else 'white')
    plt.colorbar(im,ax=ax,fraction=0.046,pad=0.04)
    ax.set_title('KPI Correlation Matrix', fontsize=8, fontweight='bold')
    plt.tight_layout()
    fig.savefig(f'{output_dir}/correlation_heatmap.png',dpi=150,bbox_inches='tight')
    plt.close(fig)

# StandardScaler is non-optional: FCF in Crore (0-50,000) vs ROE % (0-50) - without
# scaling, FCF dominates clustering entirely.
