window.SLLApi = {
  ready: false,
  desktopMode: (
    new URLSearchParams(window.location.search).get("desktop") === "1"
    || window.location.hash.replace(/^#/, "") === "desktop=1"
  ),
  _readyPromise: null,

  bridgeAvailable() {
    return Boolean(
      window.pywebview
      && window.pywebview.api
      && typeof window.pywebview.api.get_app_state === "function"
    );
  },

  waitUntilReady(timeoutMs = 15000) {
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
  }
};

window.addEventListener("pywebviewready", () => {
  window.SLLApi.ready = true;
  window.dispatchEvent(new CustomEvent("sll-api-ready"));
});
