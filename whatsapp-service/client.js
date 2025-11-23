import wwebjs from "whatsapp-web.js";
const { Client, LocalAuth } = wwebjs;
import qrcode from "qrcode-terminal";

export class WhatsAppClient {
  constructor(config = {}) {
    this.config = {
      headless: true,
      sessionName: config.sessionName || "default",
      ...config
    };
    this.client = null;
    this.isReady = false;
  }

  async initialize() {
    if (this.client) return;

    this.client = new Client({
      authStrategy: new LocalAuth({
        clientId: this.config.sessionName
      }),
      puppeteer: {
        headless: this.config.headless,
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
      },
    });

    return new Promise((resolve, reject) => {
      this.client.on("qr", (qr) => {
        console.log("[QR Code] Escaneie para autenticar:");
        qrcode.generate(qr, { small: true });
      });

      this.client.on("ready", () => {
        this.isReady = true;
        console.log("[✓] Cliente WhatsApp pronto!");
        resolve();
      });

      this.client.on("authenticated", () => {
        console.log("[✓] Cliente autenticado!");
      });

      this.client.on("disconnected", (reason) => {
        this.isReady = false;
        console.error("[✗] Desconectado:", reason);
      });

      this.client.on("error", (error) => {
        console.error("[✗] Erro do cliente:", error);
        reject(error);
      });

      this.client.initialize().catch(reject);
    });
  }

  getClient() {
    if (!this.client) {
      throw new Error("Cliente não inicializado. Chame initialize() primeiro.");
    }
    return this.client;
  }

  async logout() {
    if (this.client) {
      await this.client.logout();
      this.client = null;
      this.isReady = false;
    }
  }
}