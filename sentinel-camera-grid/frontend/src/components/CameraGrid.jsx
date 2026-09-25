import CameraCard from "./CameraCard";

export default function CameraGrid({ cameras, onSelectCamera }) {
  return (
    <section className="camera-grid">
      {cameras.map((camera) => (
        <CameraCard key={camera.providerId} camera={camera} onSelect={onSelectCamera} />
      ))}
    </section>
  );
}
