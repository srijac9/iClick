import { useEffect, useMemo, useState } from "react";
import {
  Sprout,
  Hand,
  MousePointer,
  MousePointerClick,
  Keyboard,
  Eye,
  Timer,
  Leaf,
} from "lucide-react";
import VineDecoration from "./VineDecoration";

const GESTURES = [
  { id: "blink_twice", label: "Blink Twice", icon: Eye },
  { id: "hold", label: "Hold", icon: Timer },
  { id: "open_palm", label: "Open Palm", icon: Hand },
  { id: "wave", label: "Wave", icon: Sprout },
];

const ACTIONS = [
  { id: "open_buddy", label: "Open Buddy", icon: Sprout },
  { id: "left_click", label: "Left Click", icon: MousePointer },
  { id: "right_click", label: "Right Click", icon: MousePointerClick },
  { id: "typing", label: "Typing", icon: Keyboard },
];

type MappingState = Record<string, string | null>;

const DEFAULT_MAP: MappingState = {
  blink_twice: "open_buddy",
  hold: null,
  open_palm: null,
  wave: "typing",
};

declare global {
  interface Window {
    pywebview?: {
      api: {
        load_mappings: () => Promise<MappingState>;
        save_mappings: (mappings: Array<{ gesture: string; action: string; args: Record<string, never> }>) => Promise<void>;
      };
    };
    __iclickReloadMappings?: () => void;
  }
}

function toSavePayload(mappings: MappingState) {
  return GESTURES.map((g) => ({
    gesture: g.id,
    action: mappings[g.id] || "",
    args: {},
  })).filter((m) => m.action);
}

export default function GestureGrid() {
  const [mappings, setMappings] = useState<MappingState>(DEFAULT_MAP);
  const [status, setStatus] = useState<string>("");
  const [dirty, setDirty] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const api = window.pywebview?.api;
        if (!api) return;
        const data = await api.load_mappings();
        if (mounted && data) setMappings({ ...DEFAULT_MAP, ...data });
      } catch (_e) {
        // ignore, fallback to defaults
      }
    };
    load();
    window.__iclickReloadMappings = () => {
      load();
    };
    return () => {
      mounted = false;
      delete window.__iclickReloadMappings;
    };
  }, []);

  const saveNow = async () => {
    try {
      const api = window.pywebview?.api;
      if (!api) {
        setStatus("Save unavailable");
        window.setTimeout(() => setStatus(""), 1800);
        return;
      }
      setSaving(true);
      await api.save_mappings(toSavePayload(mappings));
      setDirty(false);
      setStatus("Saved");
      window.setTimeout(() => setStatus(""), 1200);
    } catch (_e) {
      setStatus("Save failed");
      window.setTimeout(() => setStatus(""), 1800);
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    const onBeforeUnload = async () => {
      if (!dirty) return;
      try {
        const api = window.pywebview?.api;
        if (!api) return;
        await api.save_mappings(toSavePayload(mappings));
      } catch (_e) {
        // ignore
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [mappings, dirty]);

  useEffect(() => {
    window.__iclickSaveConfig = async () => {
      await saveNow();
    };
    return () => {
      delete window.__iclickSaveConfig;
    };
  }, [mappings]);

  const handleSelect = (gesture: string, action: string) => {
      setMappings((prev) => {
        let next: MappingState;
        if (prev[gesture] === action) {
          next = { ...prev, [gesture]: null };
        } else {
        next = { ...prev };
        for (const g of GESTURES) {
          if (next[g.id] === action) next[g.id] = null;
        }
        next[gesture] = action;
      }

        setDirty(true);
      return next;
    });
  };

  const statusText = useMemo(() => status, [status]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <VineDecoration />

      <div className="w-full max-w-4xl relative z-10">
        <div className="bg-card rounded-2xl border border-border shadow-2xl shadow-primary/10 vine-border overflow-hidden">
          <div className="px-8 pt-8 pb-4">
            <div className="flex items-center gap-3 mb-1">
              <div className="p-2 rounded-xl bg-primary/20">
                <Leaf className="w-6 h-6 text-vine-light" />
              </div>
              <h1 className="text-2xl font-extrabold text-foreground tracking-tight">
                Map gestures to actions
              </h1>
            </div>
            <p className="text-muted-foreground text-sm ml-14">
              Pick an action per gesture (optional).
            </p>
          </div>

          <div className="px-8 pb-8">
            <div className="grid grid-cols-5 gap-3 mb-2">
              <div className="text-sm font-bold text-muted-foreground uppercase tracking-wider py-3 px-2">
                Action
              </div>
              {GESTURES.map((gesture) => (
                <div
                  key={gesture.id}
                  className="text-center text-sm font-bold text-foreground py-3 flex flex-col items-center gap-1"
                >
                  <gesture.icon className="w-4 h-4 text-vine-light" />
                  {gesture.label}
                </div>
              ))}
            </div>

            {ACTIONS.map((action, ai) => (
              <div
                key={action.id}
                className="grid grid-cols-5 gap-3 mb-3 animate-grow"
                style={{ animationDelay: `${ai * 100}ms` }}
              >
                <div className="flex items-center gap-2 py-3 px-2">
                  <action.icon className="w-4 h-4 text-leaf shrink-0" />
                  <span className="font-semibold text-foreground text-sm">
                    {action.label}
                  </span>
                </div>

                {GESTURES.map((gesture) => {
                  const isSelected = mappings[gesture.id] === action.id;
                  return (
                    <button
                      key={gesture.id}
                      onClick={() => handleSelect(gesture.id, action.id)}
                      className={`
                        relative rounded-xl border-2 py-3 px-4 text-sm font-semibold
                        transition-all duration-300 cursor-pointer
                        ${
                          isSelected
                            ? "bg-primary border-primary text-primary-foreground shadow-lg shadow-primary/30 scale-[1.02]"
                            : "bg-secondary border-border text-secondary-foreground hover:border-vine hover:bg-muted hover:shadow-md hover:shadow-vine/10"
                        }
                      `}
                    >
                      Select
                      {isSelected && (
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-accent rounded-full animate-leaf" />
                      )}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          <div className="px-8 pb-6 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Sprout className="w-4 h-4 text-leaf animate-sway" />
              <span>iClick Shortcut Config</span>
              {dirty && <span className="ml-2 text-xs text-vine-light">Unsaved</span>}
              {statusText && <span className="ml-2 text-xs text-accent">{statusText}</span>}
            </div>
            <button
              onClick={saveNow}
              disabled={!dirty || saving}
              className={`px-4 py-2 text-xs font-semibold rounded-lg border transition-all ${
                !dirty || saving
                  ? "bg-muted text-muted-foreground border-border cursor-not-allowed"
                  : "bg-primary text-primary-foreground border-primary hover:shadow-lg hover:shadow-primary/30"
              }`}
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
