from signals.social_radar import social_radar
from config import config

def run_test():
    print("=" * 60)
    print("🔍 CHECKPOINT 4 TEST: Social & News Velocity Radar")
    print("=" * 60)
    
    symbols = config.TARGET_SYMBOLS
    print(f"Scanning sentiment velocity for underlyings: {', '.join(symbols)}...\n")
    
    for symbol in symbols:
        result = social_radar.analyze_ticker_sentiment(symbol)
        print(f"[{symbol}] Sentiment: {result['sentiment']}")
        print(f"       Bull Score: {result['bull_score']} | Bear Score: {result['bear_score']}")
        print(f"       Headlines Parsed: {result['headline_count']}")
        if result['sample_headline']:
            print(f"       Sample: \"{result['sample_headline'][:70]}...\"")
        print("-" * 50)
        
    print("\n✅ Social Radar pipeline is operational & responsive!")
    print("=" * 60)

if __name__ == "__main__":
    run_test()
