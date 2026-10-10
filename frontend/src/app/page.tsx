import Image from "next/image";
import Link from "next/link";
import { Orbit, ArrowRight } from "lucide-react";
export default function Home() {
  return (
    <main className="showcase-landing">
      <Image
        className="landing-terrain"
        unoptimized
        fill
        priority
        sizes="100vw"
        src="/api/assets/ground-navcam.jpg"
        alt="NASA Perseverance Navcam view of Mars terrain"
      />
      <div className="landing-shade" />
      <header>
        <Link className="wordmark" href="/">
          <Orbit size={22} />
          MARSENSE
        </Link>
        <span className="small-mono">THE LIVING MARS MAP</span>
      </header>
      <section aria-labelledby="intro-title">
        <p className="eyebrow">JEZERO CRATER · MISSION-CONCEPT PROTOTYPE</p>
        <h1 id="intro-title">MARSENSE</h1>
        <p className="landing-subtitle">THE LIVING MARS MAP</p>
        <div
          className="landing-sequence"
          aria-label="Expect, observe, compare, learn"
        >
          {["EXPECT", "OBSERVE", "COMPARE", "LEARN"].map((s, i) => (
            <div key={s}>
              <strong>{s}</strong>
              {i < 3 && <ArrowRight size={27} aria-hidden="true" />}
            </div>
          ))}
        </div>
        <p className="landing-copy">
          NASA tells us what we expect.
          <br />
          Astronauts show us what is actually there.
          <br />
          MARSENSE learns the difference.
        </p>
        <Link className="button landing-enter" href="/mission">
          ENTER MISSION CONTROL <ArrowRight size={16} />
        </Link>
        <p className="small muted">
          Human verification before persistent learning.
        </p>
      </section>
      <footer>
        Real cached NASA imagery · Illustrative mission geometry · Local
        prototype
      </footer>
    </main>
  );
}
