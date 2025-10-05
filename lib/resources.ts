export type SpaceResource = {
  slug: string
  title: string
  description: string
  image: string
  url: string
  category: string
  tags: string[]
}

export const spaceResources: SpaceResource[] = [
  {
    slug: "nasa-exobiology",
    title: "NASA Exobiology",
    description:
      "Research initiatives exploring the origin, evolution, distribution, and future of life in the universe, including astrobiology missions and grants.",
    image: "/placeholder.jpg",
    url: "https://science.nasa.gov/astrophysics/programs/exobiology/",
    category: "Research",
    tags: ["astrobiology", "nasa", "mission"],
  },
  {
    slug: "esa-life-support",
    title: "ESA Life Support",
    description:
      "European Space Agency research on closed-loop life support systems, regenerative habitats, and bioregenerative technologies for long-duration missions.",
    image: "/placeholder-user.jpg",
    url: "https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/Research",
    category: "Life Support",
    tags: ["esa", "life support", "bioregenerative"],
  },
  {
    slug: "iss-national-lab",
    title: "ISS National Lab Biology",
    description:
      "Access experiments, case studies, and opportunities in life sciences research conducted aboard the International Space Station National Laboratory.",
    image: "/placeholder-logo.png",
    url: "https://www.issnationallab.org/research/biology-and-biotechnology/",
    category: "Experiments",
    tags: ["iss", "biology", "microgravity"],
  },
  {
    slug: "spacex-biotech",
    title: "SpaceX Life Sciences",
    description:
      "Commercial opportunities for biotech startups leveraging SpaceX missions to conduct microgravity biology research and pharmaceutical development.",
    image: "/placeholder.svg",
    url: "https://www.spacex.com/rideshare/",
    category: "Commercial",
    tags: ["spacex", "biotech", "opportunity"],
  },
  {
    slug: "blue-origin-research",
    title: "Blue Origin Research",
    description:
      "Payload programs and research flights offered by Blue Origin for life sciences, materials, and technology demonstrations in suborbital environments.",
    image: "/placeholder-logo.svg",
    url: "https://www.blueorigin.com/",
    category: "Commercial",
    tags: ["blue origin", "research", "suborbital"],
  },
  {
    slug: "mit-space-biology",
    title: "MIT Space Biology",
    description:
      "Academic insights from MIT researchers studying cellular adaptation, synthetic biology, and human health in spaceflight conditions.",
    image: "/placeholder.jpg",
    url: "https://space.mit.edu/",
    category: "Academic",
    tags: ["mit", "synthetic biology", "academia"],
  },
]
