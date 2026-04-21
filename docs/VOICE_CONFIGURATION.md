# Voice Configuration Guide

## Auto Voice Selection

MoneyPrinterTurbo now automatically selects the best voice for your video based on the subject/topic.

## How It Works

1. **Automatic Matching**: When you create a video, the system analyzes your video subject and keywords
2. **Profile Selection**: It matches against predefined voice profiles optimized for different content types
3. **Voice Application**: The matched voice and optimal settings are automatically applied

## Configuration

### Enable/Disable Auto-Selection

Add to your `config.toml`:

```toml
[app]
# Enable automatic voice selection based on video subject (default: true)
auto_voice_selection = true

# Optional: List of voice names that trigger auto-selection
# If empty, auto-selection works for all voices
# default_voice_names = ["Graham", "Pippa"]
```

### Voice Profiles

The system includes 5 pre-configured voice profiles:

#### 1. Authoritative Male (Default for Educational Content)
- **Voice**: Graham
- **Best For**: History, Finance, Science, Documentary, True Crime, Politics
- **Speed**: 0.9x (slower for authority)
- **Example Subjects**: "The History of Ancient Rome", "Cryptocurrency Explained"

#### 2. Friendly Female (Tutorials & How-To)
- **Voice**: Pippa
- **Best For**: Tutorials, How-To, Lifestyle, Cooking, DIY, Education, Tech Reviews
- **Speed**: 1.0x (normal, clear)
- **Example Subjects**: "How to Cook Perfect Pasta", "Python Tutorial for Beginners"

#### 3. Expressive Narrator (Storytelling)
- **Voice**: Expressive_Narrator
- **Best For**: Stories, Motivation, Fiction, Drama, Reddit Stories, Entertainment
- **Speed**: 1.0x with emotional range
- **Example Subjects**: "A Day in the Life", "Inspirational Stories", "Reddit AITA"

#### 4. Professional Female (Business & News)
- **Voice**: Saanvi
- **Best For**: Business, News, Technology, Product Reviews, Analysis
- **Speed**: 1.05x (slightly faster, efficient)
- **Example Subjects**: "Tech Product Review", "Market Analysis 2026"

#### 5. Casual Male (Gaming & Commentary)
- **Voice**: Casual_Male
- **Best For**: Gaming, Vlogs, Comedy, Commentary, Reactions
- **Speed**: 1.1x (faster, conversational)
- **Example Subjects**: "Gaming Highlights", "Top 10 Fails"

## Usage Examples

### Example 1: Automatic Selection
```json
{
  "video_subject": "The Mystery of Ancient Pyramids",
  "video_script": "",
  "voice_name": "Graham"
}
```
**Result**: System detects "Ancient" + "Pyramids" → Keeps Authoritative Male voice (Graham)

### Example 2: Override Auto-Selection
```json
{
  "video_subject": "Quick Cooking Tips",
  "voice_name": "CustomVoice_123"
}
```
**Result**: Custom voice specified → Auto-selection skipped

### Example 3: Let System Decide
```json
{
  "video_subject": "How to Build a PC",
  "voice_name": "Pippa"
}
```
**Result**: Detects "How to" → Confirms Friendly Female is appropriate, uses Pippa

## Advanced: Custom Voice Profiles

You can extend the voice matcher by editing `app/services/voice_matcher.py`:

```python
VOICE_PROFILES = {
    "your_custom_profile": {
        "name": "YourVoiceName",
        "speed": 1.0,
        "stability": 0.80,
        "best_for": ["your", "keywords", "here"]
    }
}
```

## Integration with AllTalk v2

If you're using AllTalk v2, map the voice names to your AllTalk voice files:

### In voice_matcher.py:
```python
"authoritative_male": {
    "name": "male_01.wav",  # Your AllTalk voice file
    "speed": 0.9,
    ...
}
```

### Voice File Location
Place your voice files in AllTalk's voices directory, typically:
- `/path/to/alltalk/voices/`

## Troubleshooting

### Voice not changing?
1. Check `auto_voice_selection = true` in config.toml
2. Ensure you're not using a custom voice name
3. Check logs for "Auto-selected voice profile" message

### Wrong voice selected?
1. Add more specific keywords to your video subject
2. Modify the voice profile keywords in `voice_matcher.py`
3. Manually specify the voice you want

### Performance Impact
- **Negligible**: Voice matching adds <5ms to task creation
- All matching happens in Python, no external API calls

## Best Practices

1. **Specific Subjects**: Use descriptive subjects like "Tutorial: Python Functions" vs "Python"
2. **Consistent Naming**: Use consistent voice names across your AllTalk setup
3. **Test First**: Create a few test videos to see which voices match your content
4. **Monitor Logs**: Check task logs to see which voices are being selected

## API Usage

### Check what voice will be used:
```python
from app.services.voice_matcher import VoiceMatcher

profile = VoiceMatcher.match_voice_to_subject(
    subject="How to Grow Tomatoes",
    keywords="gardening tutorial"
)
print(profile)
# {'profile_id': 'friendly_female', 'voice_name': 'Pippa', 'speed': 1.0, 'stability': 0.8}
```

### List all profiles:
```python
profiles = VoiceMatcher.list_profiles()
for profile_id, profile in profiles.items():
    print(f"{profile_id}: {profile['name']} - {', '.join(profile['best_for'])}")
```
