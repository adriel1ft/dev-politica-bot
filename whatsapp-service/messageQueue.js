export class MessageQueue {
  constructor(config = {}) {
    this.queue = [];
    this.isProcessing = false;
    this.rateLimitDelay = config.rateLimitDelay || 8000;
    this.client = null;
    this.onMessageSent = config.onMessageSent || (() => {});
    this.onMessageFailed = config.onMessageFailed || (() => {});
  }

  setClient(client) {
    this.client = client;
  }

  enqueue(message) {
    if (!message.to || !message.content) {
      throw new Error("Mensagem deve ter 'to' e 'content'");
    }

    const messageItem = {
      id: `${Date.now()}-${Math.random()}`,
      to: message.to,
      content: message.content,
      metadata: message.metadata || {},
      timestamp: Date.now(),
      attempts: 0,
      maxAttempts: message.maxAttempts || 3
    };

    this.queue.push(messageItem);
    console.log(`[Fila] Mensagem enfileirada para ${messageItem.to}`);
    
    if (!this.isProcessing) {
      this.process();
    }

    return messageItem.id;
  }

  async process() {
    if (this.isProcessing || this.queue.length === 0 || !this.client?.isReady) {
      return;
    }

    this.isProcessing = true;

    while (this.queue.length > 0) {
      const messageItem = this.queue[0];

      try {
        const formattedNumber = `${messageItem.to}@c.us`;
        await this.client.getClient().sendMessage(formattedNumber, messageItem.content);
        
        console.log(`[✓] Mensagem enviada para ${messageItem.to}`);
        this.onMessageSent(messageItem);
        
        this.queue.shift();
        await this._delay(this.rateLimitDelay);
      } catch (error) {
        messageItem.attempts++;
        
        if (messageItem.attempts >= messageItem.maxAttempts) {
          console.error(`[✗] Falha ao enviar para ${messageItem.to}:`, error.message);
          this.onMessageFailed(messageItem, error);
          this.queue.shift();
        } else {
          console.warn(`[!] Tentativa ${messageItem.attempts}/${messageItem.maxAttempts} para ${messageItem.to}`);
          await this._delay(this.rateLimitDelay * messageItem.attempts);
        }
      }
    }

    this.isProcessing = false;
  }

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getStatus() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.isProcessing,
      queue: this.queue.map(msg => ({
        id: msg.id,
        to: msg.to,
        attempts: msg.attempts,
        timestamp: msg.timestamp
      }))
    };
  }

  clear() {
    this.queue = [];
  }
}