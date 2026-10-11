const https = require("https");

const TOKEN = process.env.BOT_TOKEN;

function telegram(method, data = {}) {
    return new Promise((resolve, reject) => {
        const body = JSON.stringify(data);

        const req = https.request(
            https://api.telegram.org/bot${TOKEN}/${method},
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Content-Length": Buffer.byteLength(body)
                }
            },
            res => {
                let result = "";

                res.on("data", chunk => result += chunk);
                res.on("end", () => resolve(JSON.parse(result)));
            }
        );

        req.on("error", reject);
        req.write(body);
        req.end();
    });
}

async function main() {
    console.log("Bot started!");

    let offset = 0;

    while (true) {
        const result = await telegram("getUpdates", {
            offset,
            timeout: 30
        });

        if (result.ok) {
            for (const update of result.result) {
                offset = update.update_id + 1;

                if (update.message?.text === "/start") {
                    await telegram("sendMessage", {
                        chat_id: update.message.chat.id,
                        text: "خوش اومدی عزیزم ❤️"
                    });
                }
            }
        }
    }
}

main().catch(console.error);
