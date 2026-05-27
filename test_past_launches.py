import json
from spacex_twitter_bot.config import Settings
from spacex_twitter_bot.spacex_api import SpaceXClient
from spacex_twitter_bot.model import load_model_bundle, predict_probabilities

settings = Settings.from_env()
client = SpaceXClient(base_url=settings.spacex_api_base_url)
launches = client.past_launches()

# Get the last 15 launches
recent_launches = launches[-15:]

bundle = load_model_bundle(settings.model_path)

print(f"{'Launch Name':<45} | {'Act. Launch':<11} | {'Pred. Launch':<12} | {'Act. Land':<10} | {'Pred. Land'}")
print("-" * 100)

for launch in recent_launches:
    name = launch.get("name", "Unknown")[:44]
    preds = predict_probabilities(bundle, launch)
    
    # Actual outcomes
    actual_launch = launch.get("success", False)
    
    # Check actual landing
    cores = launch.get("cores", [])
    if cores and cores[0].get("landing_attempt"):
        actual_land = cores[0].get("landing_success")
    else:
        actual_land = "N/A"
        
    pred_launch_str = f"{preds['launch_success']*100:.1f}%"
    
    if "landing_success" in preds and cores and cores[0].get("landing_attempt"):
        pred_land_str = f"{preds['landing_success']*100:.1f}%"
    else:
        pred_land_str = "N/A"
        
    print(f"{name:<45} | {str(actual_launch):<11} | {pred_launch_str:<12} | {str(actual_land):<10} | {pred_land_str}")
