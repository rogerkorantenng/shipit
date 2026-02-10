import { useEffect, useState } from 'react'

interface ConfettiProps {
  onDone: () => void
}

interface Particle {
  id: number
  x: number
  y: number
  color: string
  size: number
  rotation: number
  dx: number
  dy: number
}

const COLORS = ['#818CF8', '#F472B6', '#FBBF24', '#34D399', '#60A5FA', '#A78BFA', '#FB923C']

export default function Confetti({ onDone }: ConfettiProps) {
  const [particles, setParticles] = useState<Particle[]>([])

  useEffect(() => {
    const ps: Particle[] = []
    for (let i = 0; i < 40; i++) {
      ps.push({
        id: i,
        x: 50 + (Math.random() - 0.5) * 30,
        y: 30 + Math.random() * 10,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        size: 4 + Math.random() * 6,
        rotation: Math.random() * 360,
        dx: (Math.random() - 0.5) * 4,
        dy: -2 + Math.random() * 6,
      })
    }
    setParticles(ps)

    const timer = setTimeout(onDone, 2000)
    return () => clearTimeout(timer)
  }, [onDone])

  return (
    <div className="fixed inset-0 pointer-events-none z-[200]">
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute animate-confetti-fall"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: `${p.size}px`,
            height: `${p.size * 1.4}px`,
            backgroundColor: p.color,
            borderRadius: '2px',
            transform: `rotate(${p.rotation}deg)`,
            '--dx': `${p.dx * 40}px`,
            '--dy': `${p.dy * 80}px`,
            '--rot': `${p.rotation + 360 + Math.random() * 360}deg`,
          } as React.CSSProperties}
        />
      ))}
    </div>
  )
}
