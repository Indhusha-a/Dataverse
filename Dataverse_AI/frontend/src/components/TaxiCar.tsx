import { useRef } from "react"
import { useFrame } from "@react-three/fiber"
import { RoundedBox, ContactShadows, Sparkles, Float } from "@react-three/drei"
import * as THREE from "three"

const TAXI_YELLOW = "#ffd23f"
const BODY_DARK = "#141822"
const GLASS = "#8fd8ff"

function Wheel({ x, z }: { x: number; z: number }) {
  return (
    <group position={[x, -0.42, z]}>
      <mesh rotation={[0, 0, Math.PI / 2]} castShadow>
        <cylinderGeometry args={[0.34, 0.34, 0.26, 24]} />
        <meshStandardMaterial color="#0b0c10" roughness={0.65} metalness={0.2} />
      </mesh>
      <mesh rotation={[0, 0, Math.PI / 2]} position={[x > 0 ? 0.14 : -0.14, 0, 0]}>
        <cylinderGeometry args={[0.16, 0.16, 0.04, 20]} />
        <meshStandardMaterial color="#d9dde6" roughness={0.3} metalness={0.85} />
      </mesh>
    </group>
  )
}

function TaxiModel() {
  const group = useRef<THREE.Group>(null)
  const target = useRef({ x: 0, y: 0 })

  useFrame((state) => {
    // pointer.x/y are already normalized -1..1 by three.js relative to the canvas
    target.current.x = state.pointer.x
    target.current.y = state.pointer.y
    if (!group.current) return
    const maxYaw = Math.PI * 0.55 // wide turn, follows the cursor around
    const maxPitch = 0.16
    const desiredYaw = -target.current.x * maxYaw
    const desiredPitch = target.current.y * maxPitch
    group.current.rotation.y = THREE.MathUtils.lerp(group.current.rotation.y, desiredYaw, 0.06)
    group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, desiredPitch, 0.06)
    group.current.position.y = THREE.MathUtils.lerp(
      group.current.position.y,
      0.05 + Math.sin(state.clock.elapsedTime * 1.1) * 0.05,
      0.1,
    )
  })

  return (
    <group ref={group} dispose={null}>
      {/* Chassis */}
      <RoundedBox args={[2.1, 0.5, 1.05]} radius={0.14} smoothness={4} position={[0, -0.05, 0]} castShadow receiveShadow>
        <meshPhysicalMaterial color={TAXI_YELLOW} roughness={0.28} metalness={0.35} clearcoat={0.6} clearcoatRoughness={0.25} />
      </RoundedBox>

      {/* Checker stripe */}
      <mesh position={[0, -0.05, 0.531]}>
        <planeGeometry args={[1.9, 0.11]} />
        <meshStandardMaterial color="#0b0c10" roughness={0.5} />
      </mesh>
      <mesh position={[0, -0.05, -0.531]}>
        <planeGeometry args={[1.9, 0.11]} rotateY={Math.PI} />
        <meshStandardMaterial color="#0b0c10" roughness={0.5} side={THREE.DoubleSide} />
      </mesh>

      {/* Cabin */}
      <RoundedBox args={[1.15, 0.42, 0.92]} radius={0.12} smoothness={4} position={[-0.05, 0.42, 0]} castShadow>
        <meshPhysicalMaterial color={TAXI_YELLOW} roughness={0.28} metalness={0.35} clearcoat={0.6} />
      </RoundedBox>
      {/* Windows */}
      <RoundedBox args={[0.98, 0.24, 0.8]} radius={0.08} smoothness={4} position={[-0.05, 0.46, 0]}>
        <meshPhysicalMaterial color={GLASS} roughness={0.05} metalness={0.1} transmission={0.55} opacity={0.85} transparent ior={1.4} />
      </RoundedBox>

      {/* Taxi roof light */}
      <mesh position={[-0.05, 0.68, 0]} castShadow>
        <boxGeometry args={[0.34, 0.11, 0.16]} />
        <meshStandardMaterial color="#fff6d6" emissive="#ffdf6b" emissiveIntensity={1.6} roughness={0.3} />
      </mesh>

      {/* Bumpers */}
      <mesh position={[1.06, -0.14, 0]}>
        <boxGeometry args={[0.08, 0.22, 0.98]} />
        <meshStandardMaterial color={BODY_DARK} roughness={0.5} metalness={0.4} />
      </mesh>
      <mesh position={[-1.06, -0.14, 0]}>
        <boxGeometry args={[0.08, 0.22, 0.98]} />
        <meshStandardMaterial color={BODY_DARK} roughness={0.5} metalness={0.4} />
      </mesh>

      {/* Headlights */}
      <mesh position={[1.05, -0.02, 0.32]}>
        <sphereGeometry args={[0.07, 16, 16]} />
        <meshStandardMaterial color="#fffef2" emissive="#fff7c9" emissiveIntensity={1.4} />
      </mesh>
      <mesh position={[1.05, -0.02, -0.32]}>
        <sphereGeometry args={[0.07, 16, 16]} />
        <meshStandardMaterial color="#fffef2" emissive="#fff7c9" emissiveIntensity={1.4} />
      </mesh>
      {/* Taillights */}
      <mesh position={[-1.05, -0.02, 0.32]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="#ff5461" emissive="#ff2d3d" emissiveIntensity={1.1} />
      </mesh>
      <mesh position={[-1.05, -0.02, -0.32]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="#ff5461" emissive="#ff2d3d" emissiveIntensity={1.1} />
      </mesh>

      <Wheel x={0.72} z={0.56} />
      <Wheel x={0.72} z={-0.56} />
      <Wheel x={-0.72} z={0.56} />
      <Wheel x={-0.72} z={-0.56} />
    </group>
  )
}

export default function TaxiCar() {
  return (
    <>
      <color attach="background" args={["#06070d"]} />
      <fog attach="fog" args={["#06070d", 6, 14]} />
      <ambientLight intensity={0.55} />
      <hemisphereLight args={["#3a4a6b", "#06070d", 0.6]} />
      <directionalLight position={[3, 5, 2]} intensity={1.6} castShadow shadow-mapSize={[1024, 1024]} />
      <directionalLight position={[-2, 2, -3]} intensity={0.5} color="#8fd8ff" />
      <pointLight position={[-3, 1.5, -2]} intensity={22} color="#22d3ee" distance={8} />
      <pointLight position={[3, 1, 2.5]} intensity={14} color="#ffd23f" distance={7} />

      {/* Positioned in the upper portion of the frame, scaled down, so it reads as a
          hero visual above the headline instead of colliding with the text overlay. */}
      <group position={[0, 0.8, -0.6]} scale={0.58}>
        <Float speed={1.4} rotationIntensity={0.08} floatIntensity={0.35}>
          <TaxiModel />
        </Float>
        <ContactShadows position={[0, -0.72, 0]} opacity={0.55} scale={8} blur={2.4} far={2} color="#000000" />
      </group>
      <Sparkles count={40} scale={[9, 5, 9]} size={2} speed={0.25} opacity={0.35} color="#8fd8ff" />
    </>
  )
}
