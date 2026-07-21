window.SLLApi = {
  ready: false,
  desktopMode: (
    new URLSearchParams(window.location.search).get("desktop") === "1"
    || window.location.hash.replace(/^#/, "") === "desktop=1"
  ),
  browserBridgeMode: new URLSearchParams(window.location.search).get("transport") === "browser",
  _readyPromise: null,
  _eventCursor: 0,
  _eventPollStarted: false,

  bridgeAvailable() {
    return Boolean(
      window.pywebview
      && window.pywebview.api
      && typeof window.pywebview.api.get_app_state === "function"
    );
  },

  waitUntilReady(timeoutMs = 15000) {
    if (this.browserBridgeMode) {
      this.ready = true;
      this.startBrowserEventPolling();
      return Promise.resolve(true);
    }

    if (!this.desktopMode) {
      return Promise.resolve(false);
    }
    if (this.bridgeAvailable()) {
      this.ready = true;
      return Promise.resolve(true);
    }
    if (this._readyPromise) {
      return this._readyPromise;
    }

    this._readyPromise = new Promise((resolve, reject) => {
      let finished = false;
      let pollTimer = null;
      let timeoutTimer = null;

      const cleanup = () => {
        if (pollTimer) clearInterval(pollTimer);
        if (timeoutTimer) clearTimeout(timeoutTimer);
        window.removeEventListener("pywebviewready", onReady);
      };

      const succeed = () => {
        if (finished) return;
        finished = true;
        cleanup();
        this.ready = true;
        resolve(true);
      };

      const fail = () => {
        if (finished) return;
        finished = true;
        cleanup();
        const methods = window.pywebview?.api
          ? Object.keys(window.pywebview.api).join(", ")
          : "pywebview.api is missing";
        reject(new Error(`Python bridge did not expose get_app_state. Available: ${methods}`));
      };

      const onReady = () => {
        if (this.bridgeAvailable()) succeed();
      };

      window.addEventListener("pywebviewready", onReady);
      pollTimer = setInterval(() => {
        if (this.bridgeAvailable()) succeed();
      }, 50);
      timeoutTimer = setTimeout(fail, timeoutMs);
    });

    return this._readyPromise;
  },

  async call(method, ...args) {
    if (this.browserBridgeMode) {
      return await this.callBrowserBridge(method, ...args);
    }

    if (this.desktopMode && !this.bridgeAvailable()) {
      await this.waitUntilReady();
    }

    const apiMethod = window.pywebview?.api?.[method];
    if (typeof apiMethod === "function") {
      return await apiMethod(...args);
    }

    if (this.desktopMode) {
      throw new Error(`Python API method is unavailable: ${method}`);
    }

    // Normal-browser preview fallback only.
    if (method === "get_app_state") {
      return structuredClone(window.SLLMockState);
    }
    if (method === "select_instance") {
      const selected = window.SLLMockState.instances.find(item => item.id === args[0]) || null;
      window.SLLMockState.selected_instance_id = args[0];
      window.SLLMockState.selected_instance = selected;
      return { ok: true, state: structuredClone(window.SLLMockState) };
    }
    if (method === "set_preference") {
      window.SLLMockState.preferences[args[0]] = args[1];
      return { ok: true, preferences: structuredClone(window.SLLMockState.preferences) };
    }
    if (method === "run_action" || method === "install_official") {
      return { ok: true, started: false, preview: true };
    }
    return { ok: true, preview: true };
  },

  async callBrowserBridge(method, ...args) {
    const response = await fetch("/api/call", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ method, args })
    });

    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {}

    if (!response.ok || !payload?.ok) {
      const message = payload?.error || `Browser bridge request failed: ${method}`;
      throw new Error(message);
    }

    return payload.result;
  },

  startBrowserEventPolling() {
    if (this._eventPollStarted || !this.browserBridgeMode) return;
    this._eventPollStarted = true;

    const poll = async () => {
      try {
        const response = await fetch(`/api/events?after=${this._eventCursor}`, {
          method: "GET",
          cache: "no-store"
        });
        const payload = await response.json();
        if (payload?.ok && Array.isArray(payload.events)) {
          for (const item of payload.events) {
            this._eventCursor = Math.max(this._eventCursor, Number(item.id || 0));
            window.StoneLightBridge?.receive(item.event, item.payload);
          }
        }
      } catch (_error) {
        // The browser fallback server may be shutting down.
      } finally {
        window.setTimeout(poll, 1000);
      }
    };

    poll();
  }
};

window.addEventListener("pywebviewready", () => {
  window.SLLApi.ready = true;
  window.dispatchEvent(new CustomEvent("sll-api-ready"));
});
