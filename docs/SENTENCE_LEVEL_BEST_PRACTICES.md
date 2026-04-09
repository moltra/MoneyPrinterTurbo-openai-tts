# Sentence-Level Video Generation Best Practices

**Date:** April 9, 2026  
**Feature:** Sentence-Level Script Breakdown & Keyword Matching

---

## 🎯 Why Sentence-Level Breakdown?

### **Traditional Approach (Global Keywords)**
```
Script: "Home improvement starts with planning. Gather your tools. 
         Safety first when working with power tools."
Keywords: home improvement, tools, safety, construction
```
**Problem:** Same generic clips used throughout - boring and repetitive!

### **Sentence-Level Approach**
```
Sentence 1: "Home improvement starts with planning"
Keywords: blueprints, planning, measuring, design

Sentence 2: "Gather your tools"
Keywords: toolbox, hammer, screwdriver, drill

Sentence 3: "Safety first when working with power tools"
Keywords: safety goggles, gloves, protective gear, power drill
```
**Result:** Each sentence gets specific, relevant clips - professional and engaging! ✨

---

## 📋 Best Practices

### **1. Sentence Structure**
- **Keep sentences 8-15 words** (matches typical speech duration)
- **One idea per sentence** (easier to match clips)
- **Action-oriented language** (better visual keywords)

**Good:**
```
✅ "Mix the ingredients in a large bowl."
✅ "Heat the oven to 350 degrees."
✅ "Bake for 25 minutes until golden."
```

**Bad:**
```
❌ "Mix the ingredients, heat the oven, and bake it." (too many actions)
❌ "Do stuff." (too vague)
❌ "The process of thermally activating..." (too technical)
```

### **2. Keyword Selection**

#### **Visual Keywords First**
Focus on what can be **seen** in video clips:

**Good:**
```
Sentence: "Cut the wood with a circular saw"
Keywords: circular saw, wood cutting, sawdust, safety goggles, workshop
```

**Bad:**
```
Keywords: cutting, process, activity, work (too abstract)
```

#### **3-5 Keywords Per Sentence**
- **Primary:** Main subject (e.g., "circular saw")
- **Secondary:** Related objects (e.g., "wood plank", "sawdust")
- **Context:** Setting/mood (e.g., "workshop", "sunlight")

#### **Specificity Hierarchy**
```
Too Broad → Just Right → Too Narrow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"tool"    → "power drill" → "DeWalt 20V cordless drill"
"food"    → "pasta"       → "penne rigate from Italy"
"animal"  → "dog"         → "golden retriever puppy"
```

### **3. Keyword Categories**

For each sentence, consider these categories:

| Category | Example | Purpose |
|----------|---------|---------|
| **Object** | "hammer", "laptop" | Main subject |
| **Action** | "hammering", "typing" | What's happening |
| **Setting** | "workshop", "office" | Where it occurs |
| **Mood** | "sunrise", "calm" | Emotional tone |
| **Detail** | "close-up hands", "wide shot" | Shot composition |

**Example Sentence:**
```
Sentence: "Pour the coffee into a ceramic mug"

Object:   ceramic mug, coffee pot
Action:   pouring, steam rising
Setting:  modern kitchen, morning light
Mood:     peaceful, calm, cozy
Detail:   close-up, slow motion
```

### **4. Avoid Keyword Duplication**

**Bad (Redundant):**
```
Sentence 1: home, kitchen, cooking, chef
Sentence 2: home, kitchen, cooking, chef
Sentence 3: home, kitchen, cooking, chef
```

**Good (Specific):**
```
Sentence 1: kitchen counter, vegetables, chopping board
Sentence 2: stainless steel pot, boiling water, steam
Sentence 3: plating food, garnish, presentation
```

---

## 🔄 Workflow in WebUI

### **Step 1: Generate Script**
```
Topic: "How to make pasta"
↓
[✨ Generate Script]
↓
AI creates full script + global keywords
```

### **Step 2: Choose Review Mode**

#### **Option A: Simple Mode** (Quick)
```
✅ Use when:
- Quick projects
- Generic footage is acceptable
- Time-constrained

Review:
- Full script in one box
- Global keywords in another
```

#### **Option B: Sentence-Level Mode** (Recommended)
```
✅ Use when:
- Professional quality needed
- Precise clip matching important
- Time available for review

Review:
- Each sentence in expandable section
- Custom keywords per sentence
- Edit both text and keywords
```

### **Step 3: Review Each Sentence**

For each sentence:
1. **Read the sentence** - Does it make sense?
2. **Check keywords** - Do they match the visual content?
3. **Edit if needed** - Refine for better clip matching
4. **Check stats** - Word count, character count

**Example Review:**

```
📌 Sentence 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Start by gathering fresh ingredients."

Keywords: fresh vegetables, farmers market, 
          organic produce, shopping basket

📝 7 words  🔤 42 characters  🏷️ 4 keywords
```

### **Step 4: View Summary**
```
✅ 8 sentences • 24 unique keywords

Combined Keywords:
fresh vegetables, farmers market, organic produce,
cutting board, chef knife, mixing bowl, olive oil...
```

### **Step 5: Create Video**
Click **🎬 Create Video Task** - Video generation uses sentence-level keywords!

---

## 💡 Pro Tips

### **Tip 1: Use Synonyms Strategically**
```
Sentence 1: "man working on laptop"
Sentence 2: "person typing on computer"
Sentence 3: "professional using keyboard"

Result: Different clips, not repetitive!
```

### **Tip 2: Add Shot Type Keywords**
```
"close-up hands typing"
"wide shot office building"
"aerial view city skyline"
"slow motion coffee pouring"
```
This helps match specific camera angles!

### **Tip 3: Include Time-of-Day**
```
"sunrise mountain landscape"
"evening city lights"
"midday beach scene"
```
Better lighting consistency!

### **Tip 4: Season/Weather Context**
```
"autumn leaves falling"
"winter snow landscape"
"spring flowers blooming"
"summer beach sunset"
```
Stronger visual cohesion!

### **Tip 5: Emotion Keywords**
```
"happy family laughing"
"peaceful meditation yoga"
"energetic workout fitness"
"focused student studying"
```
Clips match the intended mood!

---

## 📊 Quality Checklist

Before creating video, verify:

- [ ] Each sentence is 8-15 words
- [ ] Each sentence has 3-5 specific keywords
- [ ] Keywords are visual (not abstract concepts)
- [ ] No excessive keyword duplication
- [ ] Keywords match sentence content
- [ ] At least one action keyword per sentence
- [ ] Context keywords (setting, mood) included
- [ ] Script flows naturally when read aloud

---

## 🎬 Example: Full Breakdown

### **Topic:** "Morning Coffee Routine"

```
📌 Sentence 1
"Wake up to the sound of the alarm clock."
Keywords: alarm clock ringing, bedroom, morning sunlight, waking up
Stats: 9 words • 48 chars • 4 keywords

📌 Sentence 2
"Walk to the kitchen and turn on the coffee maker."
Keywords: modern kitchen, coffee machine, button pressing, morning routine
Stats: 10 words • 51 chars • 4 keywords

📌 Sentence 3
"While the coffee brews, prepare your favorite mug."
Keywords: ceramic coffee mug, coffee brewing, steam rising, kitchen counter
Stats: 9 words • 52 chars • 4 keywords

📌 Sentence 4
"Pour the fresh coffee slowly into your cup."
Keywords: pouring coffee, close-up shot, steam, brown liquid, slow motion
Stats: 9 words • 44 chars • 5 keywords

📌 Sentence 5
"Add milk and sugar to taste."
Keywords: milk pouring, sugar cubes, stirring spoon, cream swirl
Stats: 6 words • 28 chars • 4 keywords

📌 Sentence 6
"Take your first sip and enjoy the rich flavor."
Keywords: drinking coffee, enjoying beverage, satisfied expression, close-up face
Stats: 9 words • 47 chars • 4 keywords
```

**Summary:**
- ✅ 6 sentences
- ✅ 25 unique keywords
- ✅ Specific visual keywords per sentence
- ✅ Natural progression
- ✅ No redundancy

**Expected Result:**
Each sentence gets perfectly matched clips:
- Sentence 1 → Alarm/waking footage
- Sentence 2 → Walking to kitchen
- Sentence 3 → Coffee machine close-up
- Sentence 4 → Pouring action (slow-mo)
- Sentence 5 → Stirring/mixing clips
- Sentence 6 → Person enjoying coffee

---

## 🚀 Advanced Techniques

### **Technique 1: Thematic Grouping**
Group related sentences for visual consistency:

```
GROUP: Introduction (Sentences 1-2)
Keywords focus: outdoor, landscape, establishing shots

GROUP: Main Content (Sentences 3-6)
Keywords focus: close-up, action, process

GROUP: Conclusion (Sentences 7-8)
Keywords focus: final product, satisfaction, wide shots
```

### **Technique 2: Shot Progression**
Plan keyword specificity for visual flow:

```
Sentence 1: "wide shot city skyline" (establish)
Sentence 2: "medium shot building entrance" (move closer)
Sentence 3: "close-up hands opening door" (detail)
Sentence 4: "interior office space" (new scene)
```

### **Technique 3: Color Coordination**
Include color keywords for cohesion:

```
Sentence 1: "blue ocean waves"
Sentence 2: "white sandy beach"
Sentence 3: "golden sunset horizon"
```
Creates a visually pleasing color palette!

---

## 📚 Keyword Library Examples

### **Business/Office**
```
laptop, computer, typing, keyboard, mouse, desk, office chair,
meeting room, presentation, whiteboard, coffee cup, notepad,
professional attire, handshake, team collaboration
```

### **Cooking**
```
cutting board, chef knife, chopping vegetables, mixing bowl,
stirring, sautéing, boiling water, oven, baking, plating,
garnish, tasting, kitchen utensils, ingredients, spices
```

### **Fitness**
```
running shoes, gym equipment, weightlifting, treadmill,
yoga mat, stretching, push-ups, water bottle, sweat,
determination, trainer, workout clothes, exercise routine
```

### **Nature**
```
forest trail, mountain peak, river flowing, waterfall,
sunrise, sunset, clouds, blue sky, green trees, wildlife,
hiking boots, backpack, camping, outdoor adventure
```

### **Technology**
```
smartphone, tablet, coding, programming, data visualization,
circuit board, robotics, LED lights, touchscreen, wireless,
innovation, futuristic, artificial intelligence, automation
```

---

## 🎯 Common Mistakes to Avoid

| Mistake | Why It's Bad | Better Approach |
|---------|--------------|-----------------|
| Too many keywords | Dilutes search, poor matches | 3-5 focused keywords |
| Abstract concepts | Hard to visualize | Use concrete objects |
| Same keywords everywhere | Repetitive clips | Vary per sentence |
| No action words | Static boring footage | Include verbs |
| Too specific | No matching clips found | Balance specificity |
| Ignoring mood | Mismatched tone | Add emotion keywords |

---

## ✅ Success Metrics

A well-structured sentence-level breakdown should achieve:

- **Clip Relevance:** 90%+ of clips match sentence content
- **Visual Variety:** Each scene has different footage
- **Flow:** Smooth transitions between sentences
- **Engagement:** Maintains viewer interest
- **Professionalism:** Looks intentionally crafted

---

## 🔗 Related Resources

- **Video Creation Workflow** - Step-by-step guide
- **Keyword Research Tools** - Finding better keywords
- **Stock Footage Sites** - Preview available clips
- **Best Practices Guide** - Overall video quality tips

---

**Remember:** Sentence-level breakdown takes a bit more time upfront, but results in MUCH higher quality videos! 🌟
