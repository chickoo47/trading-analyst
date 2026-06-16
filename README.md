# Trading Analyst

Trading Analyst is an autonomous, AI-driven financial analysis and trading framework. It utilizes a **Multi-Agent Architecture** to execute a comprehensive market analysis pipeline, debate trading strategies, and formulate precise entry and exit points.

Unlike traditional single-LLM tools, Trading Analyst structures its workflow like a real hedge fund, passing data from specialized analysts up to executive decision-makers using stateful graph logic.

## 🚀 Features

- **Multi-Agent Pipeline**: Specialized agents take on roles such as Market Analyst, News Analyst, Fundamentals Analyst, and Sentiment Analyst.
- **Risk Debate Engine**: Before a trade is executed, Risk Analysts (Bull vs. Bear) engage in a multi-round debate to stress-test the strategy.
- **Executive Portfolio Management**: Synthesizes the debate into a final structured decision (Buy, Hold, Overweight, Underweight, Sell) with precise entry points, price targets, and stop-losses.
- **Dynamic Data Acquisition**: Pulls real-time financial data, OHLCV, and news via `yfinance` and `Alpha Vantage`.
- **LLM Agnosticism**: Powered by LangChain, allowing seamless switching between OpenAI, Anthropic, Google, Groq, and local Ollama models.

## 🧠 How It Works

The framework operates in a 5-stage sequential workflow controlled by **LangGraph**:

1. **The Analyst Team**: Specialized agents pull real-time data using custom tools to generate independent technical and fundamental reports.
2. **Research Manager**: Reads the separate reports and synthesizes them into a unified "Investment Plan".
3. **The Trader**: Receives the research plan and generates a concrete "Transaction Proposal" with exact pricing.
4. **Risk Management**: Risk Analysts scrutinize the trader's proposal, debating the downsides and upsides.
5. **Portfolio Manager (The Judge)**: Reads the entire debate and outputs a final, structured decision using strict Pydantic schemas.

## 🛠 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chickoo47/trading-analyst.git
   cd trading-analyst
   ```

2. **Install dependencies:**
   Make sure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your API keys. For example, to use Groq's fast and free tier via OpenRouter:
   ```env
   TRADINGAGENTS_LLM_PROVIDER=openrouter
   TRADINGAGENTS_LLM_BACKEND_URL="https://api.groq.com/openai/v1"
   OPENROUTER_API_KEY="your_groq_api_key_here"
   ```

## 🎯 Usage

Run the main CLI interface to start the analysis process:

```bash
python -m cli.main
```

Follow the interactive prompts to:
1. Enter the ticker symbol (e.g., `AAPL`, `RELIANCE.NS`).
2. Select your Analyst Team (Market, Sentiment, News, Fundamentals).
3. Set your Research Depth (Shallow, Medium, Deep).
4. Choose your LLM Provider and Models.

Once finished, the agents will automatically generate a comprehensive `complete_report.md` in the output folder.

## ⚙️ Architecture Highlights

- **State Management**: Uses LangGraph to maintain a shared state dictionary across all nodes, allowing for complex cyclical loops like the risk debate.
- **Context Optimization**: Historical data limits and news fetch limits are strictly controlled to prevent context window overflow, making it compatible with strict free-tier API limits.
- **Structured Outputs**: Forces deterministic outputs bridging non-deterministic AI with strict trading schemas.
