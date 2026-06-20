ONLINE_WORK = {
    "freelance": {
        "title": "💼 *Freelance Platforms*\n\nWork from Ethiopia and get paid globally via verified channels:",
        "items": [
            {
                "name": "Upwork Talents",
                "desc": "Global enterprise client matrix. Ideal for language engineers, full stack programmers, and graphic asset structural designers.",
                "url":  "https://www.upwork.com",
                "tips": "💡 Comprehensive skill taxonomy mapping and clear execution portfolios scale initial project contract values."
            },
            {
                "name": "Fiverr Workspace",
                "desc": "An online platform where freelancers can sell digital services to global buyers for profit.",
                "url":  "https://www.fiverr.com",
                "tips": "💡 Set low initial prices and use highly targeted search keywords to secure your first order."
            }
        ]
    },
    "remote": {
        "title": "🌍 *Remote Job*",
        "items": [
            {
                "name": "We Work Remotely",
                "desc": "A legal and highly trusted global job board where professionals in Ethiopia can find remote, work-from-anywhere careers in tech, writing, design, and customer support.",
                "url": "https://weworkremotely.com",
                "tips": "💡 Filter your job search by selecting 'Anywhere in the World' to find high-paying international companies that actively hire remote workers living in Ethiopia."
            }
        ]
    },
    "airdrop": {
        "title": "💰 *airdrop & task*",
        "items": [
            {
                "name": "MUYA_NET_CRYPTO",
                "desc": "Your most trusted source for new and ongoing free crypto airdrops.",
                "url":  "https://t.me/MUYA_NET_CRYPTO",
                "tips": "our crypto channel."
            },
            {
                "name": "Airdrop Alert",
                "desc": "A tracking site that aggregates and verifies free cryptocurrency airdrops, giveaways, and tokens for global users.",
                "url": "https://airdropalert.com",
                "tips": "💡 Use a separate, empty crypto wallet for claims to keep your main funds completely safe from scam links."
            },
            {
                "name": "CoinMarketCap",
                "desc": "A tracking website for crypto assets that lets users monitor real-time prices and market data.",
                "url": "https://coinmarketcap.com",
                "tips": "💡 Use the free portfolio tool to track your crypto profits and losses without risking actual money."
            }
        ]
    },
    "microtask": {
        "title": "🎯 *Micro Operations*",
        "items": [
            {
                "name": "Freecash",
                "desc": "A top-rated global rewards website where users in Ethiopia can earn money by testing apps, playing mobile games, and completing simple tasks.",
                "url": "https://freecash.com/r/2OL9ED",
                "tips": " 💡 Log in every day to claim your free daily streak rewards and cash out using crypto currency."
            }
        ]
    },
    "survey": {
        "title": "📊 *Paid Surveys*",
        "items": [
            {
                "name": "Triaba Ethiopia",
                "desc": "A trusted online survey website that pays users in Ethiopia directly in cash or local mobile rewards for sharing their opinions.",
                "url": "https://triaba.com",
                "tips": "💡 Check your email inbox quickly for survey invites and answer questions honestly without rushing to avoid automated fraud filters."
            }
        ]
    },
    "youtube": {
        "title": "🎥 *Content Creation*\n\nBuild an audience and earn online:\n",
        "items": [
            {
                "name": "🎥 YouTube Channel",
                "desc": "Create videos about Ethiopian culture, tech, cooking, education, or vlogs. Monetize with ads after 1000 subscribers and 4,000 watch hours.",
                "url":  "https://www.youtube.com",
                "tips": "💡 Tip: Amharic content has a growing audience. Start with your passion topic."
            },
            {
                "name": "📸 Instagram Content",
                "desc": "Build a following around Ethiopian lifestyle, food, travel, or business. Earn through brand deals.",
                "url":  "https://www.instagram.com",
                "tips": "💡 Tip: Post consistently. 3-5 times per week is ideal for growth."
            },
            {
                "name": "✍️ Medium Writing",
                "desc": "Write articles and earn money based on how many members read your work. Pays monthly via Stripe.",
                "url":  "https://medium.com/partner-program",
                "tips": "💡 Tip: Tech, finance, and self-improvement articles perform best."
            },
            {
                "name": "🎙 Podcast Creation",
                "desc": "Start an Amharic or English podcast. Monetize through sponsorships and listener support.",
                "url":  "https://anchor.fm",
                "tips": "💡 Tip: Business, culture, and storytelling podcasts have growing Ethiopian audiences."
            },
            {
                "name": "📚 Online Teaching",
                "desc": "Teach your skills on Udemy or Teachable. Create a course once and earn passively.",
                "url":  "https://www.udemy.com/teaching",
                "tips": "💡 Tip: Ethiopian students need Amharic courses on programming, business, and finance."
            }
        ]
    }
}

def get_category(cat_key):
    return ONLINE_WORK.get(cat_key, {"title": "", "items": []})

def get_all_categories():
    return list(ONLINE_WORK.keys())
