import { useEffect, useRef } from 'react'
import * as THREE from 'three'

interface ParticleNetworkProps {
  theme: 'light' | 'dark'
}

const PARTICLE_COUNT = 120
const CONNECTION_DISTANCE = 160
const MAX_CONNECTIONS = 400
const PARTICLE_SPEED = 0.2

export default function ParticleNetwork({ theme }: ParticleNetworkProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const isDark = theme === 'dark'
    const width = window.innerWidth
    const height = window.innerHeight

    // Scene
    const scene = new THREE.Scene()

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    camera.position.z = 400

    // Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Colors
    const primaryColor = new THREE.Color(isDark ? 0xffffff : 0xd97757)
    const secondaryColor = new THREE.Color(isDark ? 0x71767b : 0xd97706)

    // Particles
    const positions = new Float32Array(PARTICLE_COUNT * 3)
    const velocities: Array<{ x: number; y: number; z: number; phase: number }> = []
    const colors = new Float32Array(PARTICLE_COUNT * 3)

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 800
      positions[i * 3 + 1] = (Math.random() - 0.5) * 800
      positions[i * 3 + 2] = (Math.random() - 0.5) * 400

      velocities.push({
        x: (Math.random() - 0.5) * PARTICLE_SPEED,
        y: (Math.random() - 0.5) * PARTICLE_SPEED,
        z: (Math.random() - 0.5) * PARTICLE_SPEED * 0.3,
        phase: Math.random() * Math.PI * 2,
      })

      const useSecondary = Math.random() > 0.75
      const c = useSecondary ? secondaryColor : primaryColor
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
    }

    const particleGeo = new THREE.BufferGeometry()
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3))

    const particleMat = new THREE.PointsMaterial({
      size: isDark ? 2.5 : 2,
      vertexColors: true,
      transparent: true,
      opacity: isDark ? 0.85 : 0.7,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    })

    const particles = new THREE.Points(particleGeo, particleMat)
    scene.add(particles)

    // Connections
    const lineGeo = new THREE.BufferGeometry()
    const linePositions = new Float32Array(MAX_CONNECTIONS * 6)
    lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3))

    const lineMat = new THREE.LineBasicMaterial({
      color: primaryColor,
      transparent: true,
      opacity: isDark ? 0.15 : 0.1,
      blending: THREE.AdditiveBlending,
    })

    const lines = new THREE.LineSegments(lineGeo, lineMat)
    scene.add(lines)

    // ============================================
    // SATURN — Glowing solid planet with ring
    // ============================================
    const saturnGroup = new THREE.Group()
    saturnGroup.position.set(260, -160, -200)
    scene.add(saturnGroup)

    // Core body (solid sphere, no wireframe)
    const saturnBodyGeo = new THREE.SphereGeometry(90, 48, 48)
    const saturnBodyMat = new THREE.MeshBasicMaterial({
      color: primaryColor,
      transparent: true,
      opacity: isDark ? 0.18 : 0.1,
      blending: THREE.AdditiveBlending,
    })
    const saturnBody = new THREE.Mesh(saturnBodyGeo, saturnBodyMat)
    saturnGroup.add(saturnBody)

    // Atmosphere glow (larger, softer)
    const saturnGlowGeo = new THREE.SphereGeometry(105, 32, 32)
    const saturnGlowMat = new THREE.MeshBasicMaterial({
      color: primaryColor,
      transparent: true,
      opacity: isDark ? 0.06 : 0.04,
      blending: THREE.AdditiveBlending,
    })
    const saturnGlow = new THREE.Mesh(saturnGlowGeo, saturnGlowMat)
    saturnGroup.add(saturnGlow)

    // Outer haze
    const saturnHazeGeo = new THREE.SphereGeometry(125, 24, 24)
    const saturnHazeMat = new THREE.MeshBasicMaterial({
      color: secondaryColor,
      transparent: true,
      opacity: isDark ? 0.03 : 0.02,
      blending: THREE.AdditiveBlending,
    })
    const saturnHaze = new THREE.Mesh(saturnHazeGeo, saturnHazeMat)
    saturnGroup.add(saturnHaze)

    // Saturn ring (torus) — thicker for visibility
    const ringGeo = new THREE.TorusGeometry(140, 7, 2, 80)
    const ringMat = new THREE.MeshBasicMaterial({
      color: isDark ? secondaryColor : primaryColor,
      transparent: true,
      opacity: isDark ? 0.25 : 0.14,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    })
    const ring = new THREE.Mesh(ringGeo, ringMat)
    ring.rotation.x = Math.PI / 2.3
    ring.rotation.y = Math.PI / 8
    saturnGroup.add(ring)

    // Outer thin ring
    const outerRingGeo = new THREE.TorusGeometry(158, 2, 2, 80)
    const outerRingMat = new THREE.MeshBasicMaterial({
      color: primaryColor,
      transparent: true,
      opacity: isDark ? 0.14 : 0.08,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    })
    const outerRing = new THREE.Mesh(outerRingGeo, outerRingMat)
    outerRing.rotation.x = Math.PI / 2.3
    outerRing.rotation.y = Math.PI / 8
    saturnGroup.add(outerRing)

    // Mouse tracking
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 }
    const onMouseMove = (e: MouseEvent) => {
      mouse.targetX = (e.clientX / window.innerWidth) * 2 - 1
      mouse.targetY = -(e.clientY / window.innerHeight) * 2 + 1
    }
    window.addEventListener('mousemove', onMouseMove)

    // Animation
    let frameId: number
    const time = { value: 0 }

    const animate = () => {
      frameId = requestAnimationFrame(animate)
      time.value += 0.008

      const posArray = particleGeo.attributes.position.array as Float32Array

      // Update particle positions
      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const v = velocities[i]
        posArray[i * 3] += v.x + Math.sin(time.value + v.phase) * 0.05
        posArray[i * 3 + 1] += v.y + Math.cos(time.value + v.phase * 0.7) * 0.05
        posArray[i * 3 + 2] += v.z

        // Wrap around
        const bounds = { x: 500, y: 500, z: 250 }
        if (posArray[i * 3] > bounds.x) posArray[i * 3] = -bounds.x
        if (posArray[i * 3] < -bounds.x) posArray[i * 3] = bounds.x
        if (posArray[i * 3 + 1] > bounds.y) posArray[i * 3 + 1] = -bounds.y
        if (posArray[i * 3 + 1] < -bounds.y) posArray[i * 3 + 1] = bounds.y
        if (posArray[i * 3 + 2] > bounds.z) posArray[i * 3 + 2] = -bounds.z
        if (posArray[i * 3 + 2] < -bounds.z) posArray[i * 3 + 2] = bounds.z
      }
      particleGeo.attributes.position.needsUpdate = true

      // Update connections
      const linePos = lineGeo.attributes.position.array as Float32Array
      let connectionIndex = 0
      const connDistSq = CONNECTION_DISTANCE * CONNECTION_DISTANCE

      for (let i = 0; i < PARTICLE_COUNT && connectionIndex < MAX_CONNECTIONS; i++) {
        for (let j = i + 1; j < PARTICLE_COUNT && connectionIndex < MAX_CONNECTIONS; j++) {
          const dx = posArray[i * 3] - posArray[j * 3]
          const dy = posArray[i * 3 + 1] - posArray[j * 3 + 1]
          const dz = posArray[i * 3 + 2] - posArray[j * 3 + 2]
          const distSq = dx * dx + dy * dy + dz * dz

          if (distSq < connDistSq) {
            const idx = connectionIndex * 6
            linePos[idx] = posArray[i * 3]
            linePos[idx + 1] = posArray[i * 3 + 1]
            linePos[idx + 2] = posArray[i * 3 + 2]
            linePos[idx + 3] = posArray[j * 3]
            linePos[idx + 4] = posArray[j * 3 + 1]
            linePos[idx + 5] = posArray[j * 3 + 2]
            connectionIndex++
          }
        }
      }

      // Hide unused lines
      for (let i = connectionIndex * 6; i < MAX_CONNECTIONS * 6; i++) {
        linePos[i] = 0
      }
      lineGeo.attributes.position.needsUpdate = true

      // Mouse parallax on camera
      mouse.x += (mouse.targetX - mouse.x) * 0.03
      mouse.y += (mouse.targetY - mouse.y) * 0.03
      camera.position.x = mouse.x * 40
      camera.position.y = mouse.y * 40
      camera.lookAt(0, 0, 0)

      // Subtle pulse on particle size
      particleMat.size = (isDark ? 2.5 : 2) + Math.sin(time.value * 3) * 0.3

      // Rotate Saturn
      saturnBody.rotation.y += 0.0015
      saturnGlow.rotation.y += 0.0012
      saturnHaze.rotation.y += 0.0008
      ring.rotation.z += 0.002
      outerRing.rotation.z += 0.002

      // Subtle floating motion for Saturn
      saturnGroup.position.y = -160 + Math.sin(time.value * 0.5) * 8
      saturnGroup.rotation.x = Math.sin(time.value * 0.3) * 0.02
      saturnGroup.rotation.y = Math.cos(time.value * 0.2) * 0.02

      renderer.render(scene, camera)
    }

    animate()

    // Resize handler
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }
    window.addEventListener('resize', onResize)

    // Cleanup
    return () => {
      cancelAnimationFrame(frameId)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('resize', onResize)
      renderer.dispose()
      particleGeo.dispose()
      particleMat.dispose()
      lineGeo.dispose()
      lineMat.dispose()
      saturnBodyGeo.dispose()
      saturnBodyMat.dispose()
      saturnGlowGeo.dispose()
      saturnGlowMat.dispose()
      saturnHazeGeo.dispose()
      saturnHazeMat.dispose()
      ringGeo.dispose()
      ringMat.dispose()
      outerRingGeo.dispose()
      outerRingMat.dispose()
      scene.remove(saturnGroup)
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [theme])

  return <div ref={containerRef} className="fixed inset-0 z-0" />
}
