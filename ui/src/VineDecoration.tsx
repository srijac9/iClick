export default function VineDecoration() {
  return (
    <>
      {/* Top-left vine */}
      <svg
        className="absolute top-0 left-0 w-64 h-64 opacity-20 animate-sway"
        viewBox="0 0 200 200"
        fill="none"
      >
        <path
          d="M0 0 Q 40 80, 20 160 Q 10 180, 30 200"
          stroke="hsl(130 40% 30%)"
          strokeWidth="3"
          fill="none"
        />
        <path
          d="M20 60 Q 50 50, 60 70"
          stroke="hsl(100 50% 40%)"
          strokeWidth="2"
          fill="none"
        />
        <circle cx="60" cy="70" r="6" fill="hsl(100 50% 40% / 0.4)" />
        <path
          d="M18 120 Q 55 100, 70 130"
          stroke="hsl(100 50% 40%)"
          strokeWidth="2"
          fill="none"
        />
        <circle cx="70" cy="130" r="5" fill="hsl(100 50% 40% / 0.3)" />
      </svg>

      {/* Bottom-right vine */}
      <svg
        className="absolute bottom-0 right-0 w-72 h-72 opacity-15"
        viewBox="0 0 200 200"
        fill="none"
        style={{ animationDelay: "1s", animation: "sway 4s ease-in-out infinite" }}
      >
        <path
          d="M200 200 Q 160 130, 180 60 Q 185 30, 170 0"
          stroke="hsl(130 40% 30%)"
          strokeWidth="3"
          fill="none"
        />
        <path
          d="M182 140 Q 145 150, 135 125"
          stroke="hsl(100 50% 40%)"
          strokeWidth="2"
          fill="none"
        />
        <circle cx="135" cy="125" r="7" fill="hsl(100 50% 40% / 0.3)" />
        <path
          d="M178 80 Q 145 70, 130 90"
          stroke="hsl(100 50% 40%)"
          strokeWidth="2"
          fill="none"
        />
        <circle cx="130" cy="90" r="5" fill="hsl(80 60% 50% / 0.4)" />
      </svg>

      {/* Scattered leaves */}
      <div className="absolute top-20 right-20 w-3 h-3 bg-leaf/20 rounded-full animate-sway" />
      <div
        className="absolute bottom-32 left-16 w-2 h-2 bg-vine-light/20 rounded-full"
        style={{ animation: "sway 5s ease-in-out infinite" }}
      />
      <div className="absolute top-1/2 right-10 w-2 h-2 bg-accent/15 rounded-full animate-sway" />
    </>
  );
}
