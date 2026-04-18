"use client"

import { Chip } from "@/components/ui/chip"
import { SearchPresetsModal, type SearchPreset, type SearchPresetsModalConfig } from"./SearchPresetsModal"

export interface LocationItem {
  value: string
  type: 'city' | 'country' | 'region'
}

export interface LocationPreset {
  id: string
  name: string
  description: string
  locations: LocationItem[]
  isOrganization?: boolean
}

const GENERAL_PRESETS: LocationPreset[] = [
  {
    id:"us_major_cities",
    name:"US Major Cities",
    description:"New York, Los Angeles, Chicago, Houston, +20 cities",
    locations: [
      { value:"New York, New York, United States", type: 'city' },
      { value:"Los Angeles, California, United States", type: 'city' },
      { value:"Chicago, Illinois, United States", type: 'city' },
      { value:"Houston, Texas, United States", type: 'city' },
      { value:"Phoenix, Arizona, United States", type: 'city' },
      { value:"Philadelphia, Pennsylvania, United States", type: 'city' },
      { value:"San Antonio, Texas, United States", type: 'city' },
      { value:"San Diego, California, United States", type: 'city' },
      { value:"Dallas, Texas, United States", type: 'city' },
      { value:"San Jose, California, United States", type: 'city' },
      { value:"Austin, Texas, United States", type: 'city' },
      { value:"Jacksonville, Florida, United States", type: 'city' },
      { value:"Fort Worth, Texas, United States", type: 'city' },
      { value:"Columbus, Ohio, United States", type: 'city' },
      { value:"Charlotte, North Carolina, United States", type: 'city' },
      { value:"Indianapolis, Indiana, United States", type: 'city' },
      { value:"Seattle, Washington, United States", type: 'city' },
      { value:"Denver, Colorado, United States", type: 'city' },
      { value:"Boston, Massachusetts, United States", type: 'city' },
      { value:"El Paso, Texas, United States", type: 'city' },
      { value:"Nashville, Tennessee, United States", type: 'city' },
      { value:"Detroit, Michigan, United States", type: 'city' },
      { value:"Portland, Oregon, United States", type: 'city' },
      { value:"Las Vegas, Nevada, United States", type: 'city' },
    ]
  },
  {
    id:"us_tech_hubs",
    name:"US Tech Hubs",
    description:"San Francisco, Seattle, Austin, Boston, +10 cities",
    locations: [
      { value:"San Francisco, California, United States", type: 'city' },
      { value:"San Jose, California, United States", type: 'city' },
      { value:"Seattle, Washington, United States", type: 'city' },
      { value:"Austin, Texas, United States", type: 'city' },
      { value:"Boston, Massachusetts, United States", type: 'city' },
      { value:"New York, New York, United States", type: 'city' },
      { value:"Denver, Colorado, United States", type: 'city' },
      { value:"Los Angeles, California, United States", type: 'city' },
      { value:"Raleigh, North Carolina, United States", type: 'city' },
      { value:"Salt Lake City, Utah, United States", type: 'city' },
      { value:"Atlanta, Georgia, United States", type: 'city' },
      { value:"Chicago, Illinois, United States", type: 'city' },
      { value:"Washington, District of Columbia, United States", type: 'city' },
      { value:"Portland, Oregon, United States", type: 'city' },
    ]
  },
  {
    id:"brazil_major_cities",
    name:"Brazil Major Cities",
    description:"São Paulo, Rio de Janeiro, Belo Horizonte, +15 cities",
    locations: [
      { value:"São Paulo, São Paulo, Brazil", type: 'city' },
      { value:"Rio de Janeiro, Rio de Janeiro, Brazil", type: 'city' },
      { value:"Belo Horizonte, Minas Gerais, Brazil", type: 'city' },
      { value:"Brasília, Distrito Federal, Brazil", type: 'city' },
      { value:"Salvador, Bahia, Brazil", type: 'city' },
      { value:"Fortaleza, Ceará, Brazil", type: 'city' },
      { value:"Curitiba, Paraná, Brazil", type: 'city' },
      { value:"Recife, Pernambuco, Brazil", type: 'city' },
      { value:"Porto Alegre, Rio Grande do Sul, Brazil", type: 'city' },
      { value:"Manaus, Amazonas, Brazil", type: 'city' },
      { value:"Goiânia, Goiás, Brazil", type: 'city' },
      { value:"Belém, Pará, Brazil", type: 'city' },
      { value:"Campinas, São Paulo, Brazil", type: 'city' },
      { value:"Florianópolis, Santa Catarina, Brazil", type: 'city' },
      { value:"São Luís, Maranhão, Brazil", type: 'city' },
      { value:"Maceió, Alagoas, Brazil", type: 'city' },
      { value:"Natal, Rio Grande do Norte, Brazil", type: 'city' },
      { value:"João Pessoa, Paraíba, Brazil", type: 'city' },
    ]
  },
  {
    id:"latin_america_capitals",
    name:"Latin America Capitals",
    description:"São Paulo, Buenos Aires, Mexico City, +10 cities",
    locations: [
      { value:"São Paulo, São Paulo, Brazil", type: 'city' },
      { value:"Buenos Aires, Buenos Aires, Argentina", type: 'city' },
      { value:"Mexico City, Ciudad de México, Mexico", type: 'city' },
      { value:"Bogotá, Bogotá, Colombia", type: 'city' },
      { value:"Lima, Lima, Peru", type: 'city' },
      { value:"Santiago, Santiago Metropolitan, Chile", type: 'city' },
      { value:"Caracas, Distrito Capital, Venezuela", type: 'city' },
      { value:"Quito, Pichincha, Ecuador", type: 'city' },
      { value:"Montevideo, Montevideo, Uruguay", type: 'city' },
      { value:"Panama City, Panamá, Panama", type: 'city' },
      { value:"San José, San José, Costa Rica", type: 'city' },
      { value:"Guatemala City, Guatemala, Guatemala", type: 'city' },
    ]
  },
  {
    id:"europe_major_cities",
    name:"Europe Major Cities",
    description:"London, Paris, Berlin, Amsterdam, +15 cities",
    locations: [
      { value:"London, England, United Kingdom", type: 'city' },
      { value:"Paris, Île-de-France, France", type: 'city' },
      { value:"Berlin, Berlin, Germany", type: 'city' },
      { value:"Amsterdam, North Holland, Netherlands", type: 'city' },
      { value:"Munich, Bavaria, Germany", type: 'city' },
      { value:"Frankfurt, Hesse, Germany", type: 'city' },
      { value:"Madrid, Community of Madrid, Spain", type: 'city' },
      { value:"Barcelona, Catalonia, Spain", type: 'city' },
      { value:"Milan, Lombardy, Italy", type: 'city' },
      { value:"Rome, Lazio, Italy", type: 'city' },
      { value:"Dublin, Leinster, Ireland", type: 'city' },
      { value:"Zurich, Zurich, Switzerland", type: 'city' },
      { value:"Vienna, Vienna, Austria", type: 'city' },
      { value:"Stockholm, Stockholm, Sweden", type: 'city' },
      { value:"Copenhagen, Capital Region, Denmark", type: 'city' },
      { value:"Brussels, Brussels-Capital, Belgium", type: 'city' },
      { value:"Warsaw, Masovian, Poland", type: 'city' },
      { value:"Prague, Prague, Czech Republic", type: 'city' },
      { value:"Lisbon, Lisbon, Portugal", type: 'city' },
    ]
  },
  {
    id:"apac_tech_hubs",
    name:"APAC Tech Hubs",
    description:"Singapore, Tokyo, Sydney, Bangalore, +8 cities",
    locations: [
      { value:"Singapore, Singapore", type: 'city' },
      { value:"Tokyo, Tokyo, Japan", type: 'city' },
      { value:"Sydney, New South Wales, Australia", type: 'city' },
      { value:"Bangalore, Karnataka, India", type: 'city' },
      { value:"Hong Kong, Hong Kong", type: 'city' },
      { value:"Shanghai, Shanghai, China", type: 'city' },
      { value:"Beijing, Beijing, China", type: 'city' },
      { value:"Shenzhen, Guangdong, China", type: 'city' },
      { value:"Seoul, Seoul, South Korea", type: 'city' },
      { value:"Melbourne, Victoria, Australia", type: 'city' },
      { value:"Mumbai, Maharashtra, India", type: 'city' },
      { value:"New Delhi, Delhi, India", type: 'city' },
    ]
  },
  {
    id:"remote_friendly_us",
    name:"Remote Friendly Timezones",
    description:"US timezones for remote work compatibility",
    locations: [
      { value:"United States", type: 'country' },
      { value:"Canada", type: 'country' },
      { value:"Mexico", type: 'country' },
    ]
  },
  {
    id:"english_speaking",
    name:"English Speaking Countries",
    description:"Primary English-speaking countries",
    locations: [
      { value:"United States", type: 'country' },
      { value:"United Kingdom", type: 'country' },
      { value:"Canada", type: 'country' },
      { value:"Australia", type: 'country' },
      { value:"Ireland", type: 'country' },
      { value:"New Zealand", type: 'country' },
    ]
  },
  {
    id:"dach_region",
    name:"DACH Region",
    description:"Germany, Austria, Switzerland",
    locations: [
      { value:"Germany", type: 'country' },
      { value:"Austria", type: 'country' },
      { value:"Switzerland", type: 'country' },
    ]
  },
  {
    id:"nordic_countries",
    name:"Nordic Countries",
    description:"Sweden, Norway, Denmark, Finland, Iceland",
    locations: [
      { value:"Sweden", type: 'country' },
      { value:"Norway", type: 'country' },
      { value:"Denmark", type: 'country' },
      { value:"Finland", type: 'country' },
      { value:"Iceland", type: 'country' },
    ]
  },
]

const toGeneric = (p: LocationPreset): SearchPreset<LocationItem> => ({
  id: p.id,
  name: p.name,
  description: p.description,
  items: p.locations,
  isOrganization: p.isOrganization,
})

const renderLocationBadges = (items: LocationItem[]) => (
  <div className="flex flex-wrap gap-1.5 mt-2">
    {items.slice(0, 4).map((loc, i) => (
      <Chip variant="neutral" muted key={i} className="bg-lia-bg-secondary text-lia-text-secondary text-micro font-normal">
        {loc.value.split(',')[0]}
      </Chip>
    ))}
    {items.length > 4 && (
      <Chip variant="neutral" muted className="bg-lia-bg-secondary text-lia-text-secondary text-micro font-normal">
        +{items.length - 4} more
      </Chip>
    )}
  </div>
)

const LOCATION_CONFIG: SearchPresetsModalConfig<LocationItem> = {
  title:"Location Presets",
  itemLabel:"locations",
  generalPresets: GENERAL_PRESETS.map(toGeneric),
  renderItemBadges: renderLocationBadges,
  saveFormPosition:"footer",
}

interface LocationPresetsModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectPreset: (locations: LocationItem[]) => void
  organizationPresets?: LocationPreset[]
  onSavePreset?: (preset: { name: string; description: string; locations: LocationItem[] }) => void
}

export function LocationPresetsModal({
  isOpen,
  onClose,
  onSelectPreset,
  organizationPresets = [],
  onSavePreset,
}: LocationPresetsModalProps) {
  return (
    <SearchPresetsModal<LocationItem>
      isOpen={isOpen}
      onClose={onClose}
      onSelectPreset={onSelectPreset}
      organizationPresets={organizationPresets.map(toGeneric)}
      onSavePreset={onSavePreset ? p => onSavePreset({ ...p, locations: [] }) : undefined}
      config={LOCATION_CONFIG}
    />
  )
}

export default LocationPresetsModal
