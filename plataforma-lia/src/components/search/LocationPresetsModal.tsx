"use client"

import { useState } from "react"
import { X, Search, Plus } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"

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
    id: "us_major_cities",
    name: "US Major Cities",
    description: "New York, Los Angeles, Chicago, Houston, +20 cities",
    locations: [
      { value: "New York, New York, United States", type: 'city' },
      { value: "Los Angeles, California, United States", type: 'city' },
      { value: "Chicago, Illinois, United States", type: 'city' },
      { value: "Houston, Texas, United States", type: 'city' },
      { value: "Phoenix, Arizona, United States", type: 'city' },
      { value: "Philadelphia, Pennsylvania, United States", type: 'city' },
      { value: "San Antonio, Texas, United States", type: 'city' },
      { value: "San Diego, California, United States", type: 'city' },
      { value: "Dallas, Texas, United States", type: 'city' },
      { value: "San Jose, California, United States", type: 'city' },
      { value: "Austin, Texas, United States", type: 'city' },
      { value: "Jacksonville, Florida, United States", type: 'city' },
      { value: "Fort Worth, Texas, United States", type: 'city' },
      { value: "Columbus, Ohio, United States", type: 'city' },
      { value: "Charlotte, North Carolina, United States", type: 'city' },
      { value: "Indianapolis, Indiana, United States", type: 'city' },
      { value: "Seattle, Washington, United States", type: 'city' },
      { value: "Denver, Colorado, United States", type: 'city' },
      { value: "Boston, Massachusetts, United States", type: 'city' },
      { value: "El Paso, Texas, United States", type: 'city' },
      { value: "Nashville, Tennessee, United States", type: 'city' },
      { value: "Detroit, Michigan, United States", type: 'city' },
      { value: "Portland, Oregon, United States", type: 'city' },
      { value: "Las Vegas, Nevada, United States", type: 'city' },
    ]
  },
  {
    id: "us_tech_hubs",
    name: "US Tech Hubs",
    description: "San Francisco, Seattle, Austin, Boston, +10 cities",
    locations: [
      { value: "San Francisco, California, United States", type: 'city' },
      { value: "San Jose, California, United States", type: 'city' },
      { value: "Seattle, Washington, United States", type: 'city' },
      { value: "Austin, Texas, United States", type: 'city' },
      { value: "Boston, Massachusetts, United States", type: 'city' },
      { value: "New York, New York, United States", type: 'city' },
      { value: "Denver, Colorado, United States", type: 'city' },
      { value: "Los Angeles, California, United States", type: 'city' },
      { value: "Raleigh, North Carolina, United States", type: 'city' },
      { value: "Salt Lake City, Utah, United States", type: 'city' },
      { value: "Atlanta, Georgia, United States", type: 'city' },
      { value: "Chicago, Illinois, United States", type: 'city' },
      { value: "Washington, District of Columbia, United States", type: 'city' },
      { value: "Portland, Oregon, United States", type: 'city' },
    ]
  },
  {
    id: "brazil_major_cities",
    name: "Brazil Major Cities",
    description: "São Paulo, Rio de Janeiro, Belo Horizonte, +15 cities",
    locations: [
      { value: "São Paulo, São Paulo, Brazil", type: 'city' },
      { value: "Rio de Janeiro, Rio de Janeiro, Brazil", type: 'city' },
      { value: "Belo Horizonte, Minas Gerais, Brazil", type: 'city' },
      { value: "Brasília, Distrito Federal, Brazil", type: 'city' },
      { value: "Salvador, Bahia, Brazil", type: 'city' },
      { value: "Fortaleza, Ceará, Brazil", type: 'city' },
      { value: "Curitiba, Paraná, Brazil", type: 'city' },
      { value: "Recife, Pernambuco, Brazil", type: 'city' },
      { value: "Porto Alegre, Rio Grande do Sul, Brazil", type: 'city' },
      { value: "Manaus, Amazonas, Brazil", type: 'city' },
      { value: "Goiânia, Goiás, Brazil", type: 'city' },
      { value: "Belém, Pará, Brazil", type: 'city' },
      { value: "Campinas, São Paulo, Brazil", type: 'city' },
      { value: "Florianópolis, Santa Catarina, Brazil", type: 'city' },
      { value: "São Luís, Maranhão, Brazil", type: 'city' },
      { value: "Maceió, Alagoas, Brazil", type: 'city' },
      { value: "Natal, Rio Grande do Norte, Brazil", type: 'city' },
      { value: "João Pessoa, Paraíba, Brazil", type: 'city' },
    ]
  },
  {
    id: "latin_america_capitals",
    name: "Latin America Capitals",
    description: "São Paulo, Buenos Aires, Mexico City, +10 cities",
    locations: [
      { value: "São Paulo, São Paulo, Brazil", type: 'city' },
      { value: "Buenos Aires, Buenos Aires, Argentina", type: 'city' },
      { value: "Mexico City, Ciudad de México, Mexico", type: 'city' },
      { value: "Bogotá, Bogotá, Colombia", type: 'city' },
      { value: "Lima, Lima, Peru", type: 'city' },
      { value: "Santiago, Santiago Metropolitan, Chile", type: 'city' },
      { value: "Caracas, Distrito Capital, Venezuela", type: 'city' },
      { value: "Quito, Pichincha, Ecuador", type: 'city' },
      { value: "Montevideo, Montevideo, Uruguay", type: 'city' },
      { value: "Panama City, Panamá, Panama", type: 'city' },
      { value: "San José, San José, Costa Rica", type: 'city' },
      { value: "Guatemala City, Guatemala, Guatemala", type: 'city' },
    ]
  },
  {
    id: "europe_major_cities",
    name: "Europe Major Cities",
    description: "London, Paris, Berlin, Amsterdam, +15 cities",
    locations: [
      { value: "London, England, United Kingdom", type: 'city' },
      { value: "Paris, Île-de-France, France", type: 'city' },
      { value: "Berlin, Berlin, Germany", type: 'city' },
      { value: "Amsterdam, North Holland, Netherlands", type: 'city' },
      { value: "Munich, Bavaria, Germany", type: 'city' },
      { value: "Frankfurt, Hesse, Germany", type: 'city' },
      { value: "Madrid, Community of Madrid, Spain", type: 'city' },
      { value: "Barcelona, Catalonia, Spain", type: 'city' },
      { value: "Milan, Lombardy, Italy", type: 'city' },
      { value: "Rome, Lazio, Italy", type: 'city' },
      { value: "Dublin, Leinster, Ireland", type: 'city' },
      { value: "Zurich, Zurich, Switzerland", type: 'city' },
      { value: "Vienna, Vienna, Austria", type: 'city' },
      { value: "Stockholm, Stockholm, Sweden", type: 'city' },
      { value: "Copenhagen, Capital Region, Denmark", type: 'city' },
      { value: "Brussels, Brussels-Capital, Belgium", type: 'city' },
      { value: "Warsaw, Masovian, Poland", type: 'city' },
      { value: "Prague, Prague, Czech Republic", type: 'city' },
      { value: "Lisbon, Lisbon, Portugal", type: 'city' },
    ]
  },
  {
    id: "apac_tech_hubs",
    name: "APAC Tech Hubs",
    description: "Singapore, Tokyo, Sydney, Bangalore, +8 cities",
    locations: [
      { value: "Singapore, Singapore", type: 'city' },
      { value: "Tokyo, Tokyo, Japan", type: 'city' },
      { value: "Sydney, New South Wales, Australia", type: 'city' },
      { value: "Bangalore, Karnataka, India", type: 'city' },
      { value: "Hong Kong, Hong Kong", type: 'city' },
      { value: "Shanghai, Shanghai, China", type: 'city' },
      { value: "Beijing, Beijing, China", type: 'city' },
      { value: "Shenzhen, Guangdong, China", type: 'city' },
      { value: "Seoul, Seoul, South Korea", type: 'city' },
      { value: "Melbourne, Victoria, Australia", type: 'city' },
      { value: "Mumbai, Maharashtra, India", type: 'city' },
      { value: "New Delhi, Delhi, India", type: 'city' },
    ]
  },
  {
    id: "remote_friendly_us",
    name: "Remote Friendly Timezones",
    description: "US timezones for remote work compatibility",
    locations: [
      { value: "United States", type: 'country' },
      { value: "Canada", type: 'country' },
      { value: "Mexico", type: 'country' },
    ]
  },
  {
    id: "english_speaking",
    name: "English Speaking Countries",
    description: "Primary English-speaking countries",
    locations: [
      { value: "United States", type: 'country' },
      { value: "United Kingdom", type: 'country' },
      { value: "Canada", type: 'country' },
      { value: "Australia", type: 'country' },
      { value: "Ireland", type: 'country' },
      { value: "New Zealand", type: 'country' },
    ]
  },
  {
    id: "dach_region",
    name: "DACH Region",
    description: "Germany, Austria, Switzerland",
    locations: [
      { value: "Germany", type: 'country' },
      { value: "Austria", type: 'country' },
      { value: "Switzerland", type: 'country' },
    ]
  },
  {
    id: "nordic_countries",
    name: "Nordic Countries",
    description: "Sweden, Norway, Denmark, Finland, Iceland",
    locations: [
      { value: "Sweden", type: 'country' },
      { value: "Norway", type: 'country' },
      { value: "Denmark", type: 'country' },
      { value: "Finland", type: 'country' },
      { value: "Iceland", type: 'country' },
    ]
  },
]

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
  onSavePreset
}: LocationPresetsModalProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [activeTab, setActiveTab] = useState<"organization" | "general">("general")
  const [showSaveForm, setShowSaveForm] = useState(false)
  const [newPresetName, setNewPresetName] = useState("")
  const [newPresetDescription, setNewPresetDescription] = useState("")

  if (!isOpen) return null

  const filteredGeneralPresets = GENERAL_PRESETS.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredOrgPresets = organizationPresets.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleSelectPreset = (preset: LocationPreset) => {
    onSelectPreset(preset.locations)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-[1px] z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-md w-full max-w-2xl max-h-[80vh] flex flex-col dark:bg-gray-800 dark:border-gray-700">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-100">Location Presets</h2>
          <button 
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search presets..."
              className="pl-9 text-sm"
            />
          </div>
        </div>

        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab("organization")}
            className={cn(
              "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "organization"
                ? "text-gray-900 dark:text-gray-100 border-b-2 border-gray-900 dark:border-gray-100"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            )}
          >
            Organization Presets
            {organizationPresets.length > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-gray-100 rounded-full">
                {organizationPresets.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("general")}
            className={cn(
              "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "general"
                ? "text-gray-900 dark:text-gray-100 border-b-2 border-gray-900 dark:border-gray-100"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            )}
          >
            General Presets
            <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-gray-100 rounded-full">
              {GENERAL_PRESETS.length}
            </span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === "organization" ? (
            filteredOrgPresets.length > 0 ? (
              <div className="grid gap-3">
                {filteredOrgPresets.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => handleSelectPreset(preset)}
                    className="w-full text-left p-3 border border-gray-200 rounded-md hover:border-gray-400 hover:bg-gray-50 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-sm font-medium text-gray-800 dark:text-gray-100">{preset.name}</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{preset.description}</p>
                      </div>
                      <Badge className="bg-gray-100 text-gray-600 text-micro">
                        {preset.locations.length} locations
                      </Badge>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {preset.locations.slice(0, 4).map((loc, i) => (
                        <Badge key={i} className="bg-gray-50 text-gray-600 text-micro font-normal">
                          {loc.value.split(',')[0]}
                        </Badge>
                      ))}
                      {preset.locations.length > 4 && (
                        <Badge className="bg-gray-50 text-gray-500 text-micro font-normal">
                          +{preset.locations.length - 4} more
                        </Badge>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {searchQuery 
                    ? "No organization presets match your search"
                    : "No organization presets yet"
                  }
                </p>
                {onSavePreset && !searchQuery && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowSaveForm(true)}
                    className="mt-3 bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700"
                  >
                    <Plus className="w-3.5 h-3.5 mr-1.5" />
                    Create Preset
                  </Button>
                )}
              </div>
            )
          ) : (
            <div className="grid gap-3">
              {filteredGeneralPresets.map(preset => (
                <button
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset)}
                  className="w-full text-left p-3 border border-gray-200 rounded-md hover:border-gray-400 hover:bg-gray-50 dark:border-gray-600 dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-all"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-800 dark:text-gray-100">{preset.name}</h3>
                      <p className="text-xs text-gray-500 mt-0.5">{preset.description}</p>
                    </div>
                    <Badge className="bg-gray-100 text-gray-600 text-micro">
                      {preset.locations.length} locations
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {preset.locations.slice(0, 4).map((loc, i) => (
                      <Badge key={i} className="bg-gray-50 text-gray-600 text-micro font-normal">
                        {loc.value.split(',')[0]}
                      </Badge>
                    ))}
                    {preset.locations.length > 4 && (
                      <Badge className="bg-gray-50 text-gray-500 text-micro font-normal">
                        +{preset.locations.length - 4} more
                      </Badge>
                    )}
                  </div>
                </button>
              ))}
              {filteredGeneralPresets.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-500">No presets match your search</p>
                </div>
              )}
            </div>
          )}
        </div>

        {showSaveForm && onSavePreset && (
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700">
            <Label className="text-xs font-medium text-gray-800 dark:text-gray-200">Create New Preset</Label>
            <div className="flex gap-2 mt-2">
              <Input
                value={newPresetName}
                onChange={(e) => setNewPresetName(e.target.value)}
                placeholder="Preset name"
                className="text-sm"
              />
              <Input
                value={newPresetDescription}
                onChange={(e) => setNewPresetDescription(e.target.value)}
                placeholder="Description"
                className="text-sm"
              />
              <Button
                size="sm"
                onClick={() => {
                  if (newPresetName.trim()) {
                    onSavePreset({
                      name: newPresetName.trim(),
                      description: newPresetDescription.trim(),
                      locations: []
                    })
                    setNewPresetName("")
                    setNewPresetDescription("")
                    setShowSaveForm(false)
                  }
                }}
                className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                Save
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowSaveForm(false)
                  setNewPresetName("")
                  setNewPresetDescription("")
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default LocationPresetsModal
