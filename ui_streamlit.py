"""AI-Powered Trading System — Streamlit UI.

Tabs:
  1. Backtest          — run rule-based or ML-based back-tests
  2. AI / ML Analytics — feature importance charts & ML documentation
  3. Optimization      — Optuna hyper-parameter search
"""

import os
import sys

import pandas as pd
import streamlit as st

# ── Path so we can import project modules directly ─────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.services.ai.feature_service import feature_service  # noqa: E402

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar — Global Config ────────────────────────────────────────────────────
st.sidebar.title("⚙️ Configuration")

STANDARD_STRATEGIES = [
    "MovingAverageCrossover",
    "RSIMeanReversion",
    "MACDCrossover",
    "TrendPullback",
    "CandleCombined",
]
ML_STRATEGIES = [
    "XGBoostPredictor (ML)",
    "RandomForestPredictor (ML)",
]
ALL_STRATEGIES = STANDARD_STRATEGIES + ML_STRATEGIES

selected_strategy = st.sidebar.selectbox(
    "Select Strategy",
    ALL_STRATEGIES,
    help=(
        "Choose a standard rules-based strategy or a predictive ML model "
        "trained on historical data. "
        "ML strategies require a pre-trained model saved in ML_MODEL_DIR."
    ),
)

is_ml_strategy = selected_strategy in ML_STRATEGIES

symbol = st.sidebar.text_input(
    "Symbol",
    value="AAPL",
    help="Ticker symbol to backtest (e.g. AAPL, TSLA, SPY).",
)

col1, col2 = st.sidebar.columns(2)
start_date = col1.date_input("Start Date", value=pd.Timestamp("2022-01-01"))
end_date = col2.date_input("End Date", value=pd.Timestamp("2024-01-01"))

initial_capital = st.sidebar.number_input(
    "Initial Capital ($)",
    min_value=1_000,
    value=100_000,
    step=1_000,
    help="Starting account value in USD.",
)

# ML-only sidebar params
if is_ml_strategy:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 ML Parameters")

    lookback_window = st.sidebar.number_input(
        "Lookback Window (days)",
        min_value=10,
        max_value=252,
        value=50,
        help=(
            "Number of previous days the ML model observes to calculate "
            "technical indicators and pattern matching."
        ),
    )

    prediction_horizon = st.sidebar.number_input(
        "Prediction Horizon (days)",
        min_value=1,
        max_value=30,
        value=5,
        help="Number of forward days the model is trained to predict.",
    )

    model_name_input = st.sidebar.text_input(
        "Model Name",
        value="my_model",
        help=(
            "Name of the .joblib model file inside ML_MODEL_DIR. "
            "Train and save a model using predictor.save('my_model')."
        ),
    )

# ── Main Tabs ──────────────────────────────────────────────────────────────────
tab_backtest, tab_ml, tab_optim = st.tabs(
    ["📊 Backtest", "🤖 AI / ML Analytics", "🔬 Optimization"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BACKTEST
# ═══════════════════════════════════════════════════════════════════════════════
with tab_backtest:
    st.header(f"Backtest — {selected_strategy}")

    if is_ml_strategy:
        st.info(
            "**ML Strategy selected.** Make sure a trained model is saved at "
            f"`ML_MODEL_DIR/{model_name_input}.joblib` before running the backtest."
        )

    if st.button("▶  Run Backtest", type="primary"):
        with st.spinner("Running backtest…"):
            st.warning(
                "Live backtest execution requires a running backend server. "
                "Connect this button to `POST /api/v1/backtest` to run a real backtest."
            )

    st.markdown("---")
    st.subheader("How It Works")
    st.markdown(
        """
        1. Select a strategy and parameters in the sidebar.
        2. Click **Run Backtest** to execute against historical price data.
        3. Results are displayed as an equity curve, trade log, and summary metrics.
        """
    )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — AI / ML ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ml:
    st.header("🤖 AI / ML Analytics")

    # ── Model Selector ────────────────────────────────────────────────────────
    available_models = feature_service.list_available_models()
    model_dir = os.environ.get("ML_MODEL_DIR", "ml_models")

    if available_models:
        selected_model = st.selectbox(
            "Select Trained Model",
            available_models,
            help=(
                f"Models found in `{model_dir}/`. "
                "Train and save a model with `predictor.save('name')` to populate this list."
            ),
        )
    else:
        st.warning(
            f"No trained models found in `{model_dir}/`. "
            "Train a model and save it with `predictor.save('name')` to enable this section."
        )
        selected_model = st.text_input(
            "Or enter a model name manually",
            value="my_model",
            help="Type the base name (without .joblib) of a model file.",
        )

    # ── Feature Importance Chart ──────────────────────────────────────────────
    st.subheader("📊 Feature Importances")

    if st.button("Load Feature Importances"):
        with st.spinner(f"Loading model '{selected_model}'…"):
            payload = feature_service.get_feature_importance(selected_model)

        if payload.get("error"):
            st.error(payload["error"])
        elif payload["feature_importances"]:
            fi_df = pd.DataFrame(payload["feature_importances"])
            fi_df["importance"] = fi_df["importance"].astype(float)
            fi_df = fi_df.sort_values("importance", ascending=False).set_index("feature")

            st.bar_chart(fi_df["importance"])

            with st.expander("Raw Data"):
                st.dataframe(
                    fi_df.reset_index().rename(
                        columns={"feature": "Feature", "importance": "Importance Score"}
                    ),
                    use_container_width=True,
                )
        else:
            st.info("No feature importances returned for this model.")

    st.markdown("---")

    # ── How to Use — Documentation Expanders ─────────────────────────────────
    st.subheader("📖 How to Use ML Features")

    with st.expander("🏋️ Model Training"):
        st.markdown(
            "Before running a backtest with an ML Strategy, ensure a model is trained. "
            "The system uses historical OHLCV data to create features (like RSI and MACD) "
            "and trains a gradient boosted tree to predict forward returns."
        )
        st.code(
            """\
from strategy_lab.ml.features import TimeSeriesFeatureGenerator
from strategy_lab.ml.models.tree_models import XGBoostPredictor
import yfinance as yf

# 1. Fetch data
df = yf.download("AAPL", start="2020-01-01", end="2024-01-01")
df.columns = df.columns.get_level_values(0)  # flatten multi-index

# 2. Generate features & targets
gen = TimeSeriesFeatureGenerator()
X = gen.generate_features(df).dropna()
y = gen.generate_targets(df).reindex(X.index).dropna()
X = X.reindex(y.index)

# 3. Train & save
model = XGBoostPredictor()
model.train(X, y)
model.save("aapl_xgb")   # writes to ML_MODEL_DIR/aapl_xgb.joblib
""",
            language="python",
        )

    with st.expander("📊 Feature Importance"):
        st.markdown(
            "This chart shows which technical indicators the AI relies on most. "
            "A higher score means the model heavily weights this feature when "
            "deciding to Buy, Sell, or Hold."
        )

    with st.expander("🔍 Pattern Recognition"):
        st.markdown(
            "The ML engine matches current market conditions to historical regimes. "
            "If the current volatility and trend match a historical 'bull flag', "
            "the model's confidence score increases."
        )

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════════
with tab_optim:
    st.header("🔬 Hyperparameter Optimization (Optuna)")

    st.info(
        "The optimization engine uses **Optuna with MedianPruner** to automatically "
        "search for the best strategy parameters. Unpromising trials are killed early, "
        "saving significant compute time."
    )

    n_trials = st.number_input(
        "Number of Trials",
        min_value=5,
        max_value=500,
        value=50,
        help="How many hyperparameter combinations Optuna will evaluate.",
    )

    if st.button("▶  Start Optimization", type="primary"):
        with st.spinner("Running Optuna optimization…"):
            st.warning(
                "Live optimization requires a running backend server. "
                "Connect this button to `POST /api/v1/optimize` to run real optimization."
            )
