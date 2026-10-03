const VIDEO_EXT = /\.(mp4|webm|m4v|mov)(\?.*)?$/i
const YOUTUBE = /(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{11})/i

// A gallery entry is just a URL; its type is inferred so the backend needs no
// extra column. Returns { kind: 'image' | 'video' | 'youtube', url, youtubeId? }.
export function classifyMedia(url) {
  const yt = YOUTUBE.exec(url)
  if (yt) return { kind: 'youtube', url, youtubeId: yt[1] }
  if (VIDEO_EXT.test(url)) return { kind: 'video', url }
  return { kind: 'image', url }
}

export function youtubeThumb(id) {
  return `https://img.youtube.com/vi/${id}/mqdefault.jpg`
}

export function youtubeEmbed(id) {
  return `https://www.youtube-nocookie.com/embed/${id}`
}
