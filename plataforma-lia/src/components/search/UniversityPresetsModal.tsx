"use client"

import { useState, useEffect } from "react"
import { X, Search, Plus, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"

export interface UniversityPreset {
  id: string
  name: string
  description: string
  universities: string[]
  isOrganization?: boolean
}

const GENERAL_PRESETS: UniversityPreset[] = [
  {
    id: "ivy_league",
    name: "Ivy League",
    description: "The eight prestigious Ivy League universities",
    universities: [
      "Harvard University",
      "Yale University",
      "Princeton University",
      "Columbia University",
      "Brown University",
      "Cornell University",
      "Dartmouth College",
      "University of Pennsylvania"
    ]
  },
  {
    id: "us_top_100",
    name: "US Top 100",
    description: "Based on US News 2024 Rankings",
    universities: [
      "Harvard University", "Stanford University", "MIT", "Yale University", "Princeton University",
      "Columbia University", "University of Pennsylvania", "Caltech", "Duke University", "Northwestern University",
      "Johns Hopkins University", "Brown University", "Cornell University", "University of Chicago", "Rice University",
      "Dartmouth College", "Vanderbilt University", "University of Notre Dame", "UCLA", "UC Berkeley",
      "University of Michigan", "Carnegie Mellon University", "Emory University", "Georgetown University", "NYU",
      "University of Virginia", "USC", "Wake Forest University", "University of Florida", "University of North Carolina",
      "Boston College", "Tufts University", "University of Rochester", "Boston University", "Case Western Reserve University",
      "University of Wisconsin-Madison", "University of Texas at Austin", "University of Illinois Urbana-Champaign",
      "Georgia Institute of Technology", "Ohio State University", "Purdue University", "Penn State University",
      "University of Washington", "University of Maryland", "Texas A&M University", "University of Minnesota",
      "University of Pittsburgh", "Rutgers University", "Michigan State University", "University of Arizona"
    ]
  },
  {
    id: "us_top_50_cs",
    name: "US Top 50 CS",
    description: "Top Computer Science programs in the US",
    universities: [
      "MIT", "Stanford University", "Carnegie Mellon University", "UC Berkeley", "University of Illinois Urbana-Champaign",
      "Cornell University", "University of Washington", "Princeton University", "Georgia Institute of Technology", "Caltech",
      "University of Michigan", "University of Texas at Austin", "Columbia University", "UCLA", "University of Wisconsin-Madison",
      "Harvard University", "University of Maryland", "University of Pennsylvania", "Purdue University", "USC",
      "Yale University", "Duke University", "Northwestern University", "Brown University", "NYU",
      "Rice University", "University of Massachusetts Amherst", "Ohio State University", "University of Minnesota",
      "University of Virginia", "Penn State University", "Rutgers University", "University of California San Diego",
      "University of California Irvine", "University of California Davis", "Boston University", "Northeastern University",
      "University of Colorado Boulder", "University of Utah", "University of North Carolina", "Virginia Tech",
      "Arizona State University", "University of Arizona", "University of Florida", "Johns Hopkins University",
      "Stony Brook University", "University of California Santa Barbara", "Indiana University", "University of Notre Dame",
      "Rochester Institute of Technology"
    ]
  },
  {
    id: "us_top_50_business",
    name: "US Top 50 Business",
    description: "Top Business Schools in the US",
    universities: [
      "Harvard Business School", "Stanford GSB", "Wharton (University of Pennsylvania)", "MIT Sloan",
      "Columbia Business School", "Kellogg (Northwestern University)", "Booth (University of Chicago)",
      "Haas (UC Berkeley)", "Tuck (Dartmouth College)", "Yale School of Management",
      "Ross (University of Michigan)", "Darden (University of Virginia)", "Fuqua (Duke University)",
      "Stern (NYU)", "Anderson (UCLA)", "Johnson (Cornell University)", "Tepper (Carnegie Mellon University)",
      "McCombs (University of Texas at Austin)", "Goizueta (Emory University)", "Georgetown McDonough",
      "Kenan-Flagler (UNC)", "Marshall (USC)", "Foster (University of Washington)", "Kelley (Indiana University)",
      "Mendoza (University of Notre Dame)", "Fisher (Ohio State University)", "Carlson (University of Minnesota)",
      "Questrom (Boston University)", "Scheller (Georgia Tech)", "Mays (Texas A&M University)",
      "Olin (Washington University)", "Smith (University of Maryland)", "Broad (Michigan State University)",
      "Marriott (BYU)", "Smeal (Penn State)", "Wisconsin School of Business", "Owen (Vanderbilt University)",
      "Jones (Rice University)", "Krannert (Purdue University)", "Kogod (American University)",
      "Eller (University of Arizona)", "Daniels (University of Denver)", "Freeman (Tulane University)",
      "Farmer (Miami University)", "Lindner (University of Cincinnati)", "Gatton (University of Kentucky)",
      "Pamplin (Virginia Tech)", "Warrington (University of Florida)", "Henry B. Tippie (University of Iowa)",
      "Babson College"
    ]
  },
  {
    id: "uk_top_30",
    name: "UK Top 30",
    description: "Top universities in the United Kingdom",
    universities: [
      "University of Oxford", "University of Cambridge", "Imperial College London", "London School of Economics",
      "University College London", "University of Edinburgh", "King's College London", "University of Manchester",
      "University of Bristol", "University of Warwick", "University of Glasgow", "Durham University",
      "University of Southampton", "University of Birmingham", "University of Leeds", "University of Nottingham",
      "University of Sheffield", "University of St Andrews", "Queen Mary University of London", "Lancaster University",
      "Newcastle University", "University of York", "University of Exeter", "Cardiff University",
      "University of Bath", "University of Liverpool", "University of Reading", "Queen's University Belfast",
      "University of Sussex", "SOAS University of London"
    ]
  },
  {
    id: "europe_top_50",
    name: "Europe Top 50",
    description: "Top universities across Europe",
    universities: [
      "ETH Zurich", "EPFL", "University of Oxford", "University of Cambridge", "Imperial College London",
      "London School of Economics", "University College London", "Technical University of Munich",
      "Ludwig Maximilian University of Munich", "Heidelberg University", "Karolinska Institute",
      "University of Amsterdam", "Delft University of Technology", "PSL Research University Paris",
      "Sorbonne University", "École Polytechnique", "Sciences Po", "HEC Paris", "INSEAD",
      "University of Copenhagen", "KU Leuven", "Wageningen University", "University of Zurich",
      "University of Barcelona", "Pompeu Fabra University", "Bocconi University", "Politecnico di Milano",
      "University of Helsinki", "Uppsala University", "Lund University", "University of Oslo",
      "Trinity College Dublin", "University of Vienna", "Humboldt University of Berlin",
      "Free University of Berlin", "Technical University of Berlin", "University of Bonn",
      "University of Freiburg", "University of Tübingen", "Erasmus University Rotterdam",
      "Leiden University", "University of Groningen", "Utrecht University", "Vrije Universiteit Amsterdam",
      "University of Edinburgh", "University of Manchester", "King's College London", "Warwick University",
      "University of Bristol", "University of Glasgow"
    ]
  },
  {
    id: "asia_top_50",
    name: "Asia Top 50",
    description: "Top universities across Asia",
    universities: [
      "Tsinghua University", "Peking University", "National University of Singapore", "Nanyang Technological University",
      "University of Hong Kong", "HKUST", "Chinese University of Hong Kong", "Seoul National University",
      "KAIST", "Yonsei University", "Korea University", "University of Tokyo", "Kyoto University",
      "Tokyo Institute of Technology", "Osaka University", "Tohoku University", "Indian Institute of Technology Delhi",
      "Indian Institute of Technology Bombay", "Indian Institute of Technology Madras", "Indian Institute of Science",
      "Fudan University", "Shanghai Jiao Tong University", "Zhejiang University", "Nanjing University",
      "University of Science and Technology of China", "Harbin Institute of Technology", "Xi'an Jiaotong University",
      "Wuhan University", "Sun Yat-sen University", "Huazhong University of Science and Technology",
      "National Taiwan University", "POSTECH", "Sungkyunkwan University", "Hanyang University",
      "Hong Kong Polytechnic University", "City University of Hong Kong", "Keio University", "Waseda University",
      "Nagoya University", "Kyushu University", "Hokkaido University", "Indian Institute of Technology Kanpur",
      "Indian Institute of Technology Kharagpur", "University of Delhi", "Jawaharlal Nehru University",
      "University of Malaya", "Universiti Teknologi Malaysia", "Chulalongkorn University",
      "Mahidol University", "Vietnam National University"
    ]
  },
  {
    id: "brazil_top_30",
    name: "Brazil Top 30",
    description: "Top universities in Brazil",
    universities: [
      "USP (Universidade de São Paulo)", "Unicamp", "UFRJ", "UFMG", "UFRGS",
      "UFSC", "UnB", "UFPR", "UNESP", "UFSCar",
      "UFPE", "UFC", "UFBA", "PUC-Rio", "FGV",
      "Insper", "ITA", "IME", "Mackenzie", "UERJ",
      "UNIFESP", "UFV", "UFF", "UFES", "UFSM",
      "PUCRS", "PUC-SP", "UFCG", "UFG", "UFRN"
    ]
  },
  {
    id: "latin_america_top_50",
    name: "Latin America Top 50",
    description: "Top universities across Latin America",
    universities: [
      "USP (Universidade de São Paulo)", "Unicamp", "UFRJ", "PUC-Chile", "Universidad de Chile",
      "ITESM (Tecnológico de Monterrey)", "UNAM", "Universidad de Buenos Aires", "Universidad de los Andes Colombia",
      "Universidad Nacional de Colombia", "Universidade Federal de Minas Gerais", "UFRGS",
      "Universidad de Concepción", "Universidad Diego Portales", "Universidad Católica Argentina",
      "Universidad Torcuato Di Tella", "Universidad de San Andrés", "UFSC", "UnB", "UNESP",
      "PUC-Rio", "FGV", "Universidad del Pacífico Peru", "PUCP (Peru)", "Universidad de Lima",
      "Universidad EAFIT", "Universidad del Norte Colombia", "Universidad de Antioquia",
      "Universidad Iberoamericana Mexico", "ITAM", "Universidad Panamericana", "UAM (Mexico)",
      "IPN (Mexico)", "Universidad de Guadalajara", "Universidad Autónoma de Nuevo León",
      "Universidad de Costa Rica", "TEC Costa Rica", "Universidad de Puerto Rico",
      "Universidad Católica del Uruguay", "Universidad ORT Uruguay", "Universidad de la República",
      "Universidad Católica Boliviana", "Universidad Mayor de San Andrés", "ESPOL (Ecuador)",
      "Universidad San Francisco de Quito", "USFQ", "Universidad Central de Venezuela",
      "Universidad Simón Bolívar", "Universidad Metropolitana Venezuela", "USB"
    ]
  },
  {
    id: "africa_top_50",
    name: "Africa Top 50",
    description: "Top universities across Africa",
    universities: [
      "University of Cape Town", "University of Witwatersrand", "Stellenbosch University",
      "University of Pretoria", "University of Johannesburg", "Rhodes University",
      "University of KwaZulu-Natal", "Cairo University", "American University in Cairo",
      "Ain Shams University", "Alexandria University", "University of Nairobi",
      "Strathmore University", "Makerere University", "University of Ghana",
      "Kwame Nkrumah University of Science and Technology", "University of Lagos",
      "Covenant University", "University of Ibadan", "Obafemi Awolowo University",
      "University of Nigeria Nsukka", "American University of Nigeria", "Addis Ababa University",
      "University of Dar es Salaam", "University of Rwanda", "National University of Rwanda",
      "University of Mauritius", "University of Botswana", "University of Zimbabwe",
      "University of Zambia", "Copperbelt University", "University of Malawi",
      "Eduardo Mondlane University", "University of Namibia", "University of Swaziland",
      "Cheikh Anta Diop University", "Mohammed V University", "Al Akhawayn University",
      "University of Tunisia", "Tunis El Manar University", "University of Algiers",
      "University of Constantine", "University of Oran", "Mansoura University",
      "Assiut University", "Suez Canal University", "Benha University",
      "Port Said University", "Université Félix Houphouët-Boigny", "USTTB Mali"
    ]
  },
  {
    id: "aus_nzl_top_20",
    name: "AUS/NZL Top 20",
    description: "Top universities in Australia and New Zealand",
    universities: [
      "University of Melbourne", "University of Sydney", "Australian National University",
      "University of Queensland", "University of New South Wales", "Monash University",
      "University of Western Australia", "University of Adelaide", "University of Auckland",
      "University of Otago", "Victoria University of Wellington", "University of Canterbury",
      "Macquarie University", "University of Technology Sydney", "RMIT University",
      "University of Wollongong", "Queensland University of Technology", "Curtin University",
      "Deakin University", "Griffith University"
    ]
  },
  {
    id: "india_top_20",
    name: "India Top 20",
    description: "Top universities and institutes in India",
    universities: [
      "Indian Institute of Technology Delhi", "Indian Institute of Technology Bombay",
      "Indian Institute of Technology Madras", "Indian Institute of Technology Kanpur",
      "Indian Institute of Technology Kharagpur", "Indian Institute of Science",
      "Indian Institute of Technology Roorkee", "Indian Institute of Technology Guwahati",
      "Indian Institute of Technology Hyderabad", "Indian Institute of Technology BHU",
      "Indian Institute of Management Ahmedabad", "Indian Institute of Management Bangalore",
      "Indian Institute of Management Calcutta", "Indian Institute of Management Lucknow",
      "Delhi University", "Jawaharlal Nehru University", "BITS Pilani",
      "National Institute of Technology Trichy", "Anna University", "Jadavpur University"
    ]
  },
  {
    id: "middle_east_top_20",
    name: "Middle East Top 20",
    description: "Top universities in the Middle East",
    universities: [
      "Tel Aviv University", "Hebrew University of Jerusalem", "Technion",
      "Weizmann Institute of Science", "Ben-Gurion University", "King Saud University",
      "King Abdulaziz University", "King Abdullah University of Science and Technology",
      "American University of Beirut", "Lebanese American University",
      "Qatar University", "Khalifa University", "United Arab Emirates University",
      "American University of Sharjah", "University of Tehran", "Sharif University of Technology",
      "Amirkabir University of Technology", "Bilkent University", "Koç University",
      "Middle East Technical University"
    ]
  },
  {
    id: "global_top_100",
    name: "Global Top 100",
    description: "Based on Times Higher Education World University Rankings",
    universities: [
      "Harvard University", "Stanford University", "MIT", "Oxford University", "Cambridge University",
      "Caltech", "Princeton University", "University of Chicago", "Imperial College London", "Yale University",
      "ETH Zurich", "Columbia University", "University of Pennsylvania", "Johns Hopkins University", "UCLA",
      "UC Berkeley", "Duke University", "Cornell University", "Northwestern University", "University of Michigan",
      "NYU", "University of Toronto", "Carnegie Mellon University", "University of Washington", "London School of Economics",
      "University College London", "University of Edinburgh", "National University of Singapore", "Tsinghua University",
      "Peking University", "University of Tokyo", "Kyoto University", "Seoul National University", "KAIST",
      "Nanyang Technological University", "University of Hong Kong", "HKUST", "Chinese University of Hong Kong",
      "University of Melbourne", "Australian National University", "University of Sydney", "University of Queensland",
      "Monash University", "University of British Columbia", "McGill University", "Technical University of Munich",
      "LMU Munich", "EPFL", "PSL University Paris", "Sorbonne University", "King's College London",
      "University of Manchester", "University of Bristol", "Karolinska Institute", "University of Amsterdam",
      "Delft University of Technology", "KU Leuven", "University of Zurich", "Heidelberg University",
      "Fudan University", "Shanghai Jiao Tong University", "Zhejiang University", "University of Science and Technology of China",
      "National Taiwan University", "Pohang University of Science and Technology", "Yonsei University",
      "Indian Institute of Science", "IIT Delhi", "IIT Bombay", "University of Auckland", "University of Cape Town",
      "University of Witwatersrand", "American University in Cairo", "USP", "Unicamp", "UFRJ",
      "PUC-Chile", "Universidad de Chile", "University of Buenos Aires", "UNAM", "Tecnológico de Monterrey"
    ]
  },
  {
    id: "hbcus",
    name: "HBCUs",
    description: "Historically Black Colleges and Universities",
    universities: [
      "Howard University", "Spelman College", "Morehouse College", "Hampton University",
      "Tuskegee University", "Florida A&M University", "North Carolina A&T State University",
      "Xavier University of Louisiana", "Clark Atlanta University", "Tennessee State University",
      "Morgan State University", "Alabama State University", "Jackson State University",
      "Southern University", "Grambling State University", "Prairie View A&M University",
      "Delaware State University", "Bethune-Cookman University", "Fisk University",
      "Dillard University"
    ]
  },
  {
    id: "women_colleges",
    name: "Women's Colleges",
    description: "Top women's colleges in the US (Seven Sisters and more)",
    universities: [
      "Wellesley College", "Smith College", "Barnard College", "Bryn Mawr College",
      "Mount Holyoke College", "Vassar College", "Radcliffe College", "Scripps College",
      "Mills College", "Agnes Scott College", "Simmons University", "Sweet Briar College",
      "Hollins University", "Spelman College", "Bennett College", "Cedar Crest College"
    ]
  },
  {
    id: "liberal_arts_top_20",
    name: "Liberal Arts Top 20",
    description: "Top liberal arts colleges in the US",
    universities: [
      "Williams College", "Amherst College", "Swarthmore College", "Wellesley College",
      "Pomona College", "Bowdoin College", "Claremont McKenna College", "Middlebury College",
      "Carleton College", "Washington and Lee University", "Haverford College", "Colby College",
      "Davidson College", "Hamilton College", "Wesleyan University", "Grinnell College",
      "Colgate University", "Harvey Mudd College", "Bates College", "Smith College"
    ]
  },
  {
    id: "engineering_top_20",
    name: "Engineering Top 20",
    description: "Top engineering schools globally",
    universities: [
      "MIT", "Stanford University", "Caltech", "UC Berkeley", "Carnegie Mellon University",
      "Georgia Institute of Technology", "University of Michigan", "University of Illinois Urbana-Champaign",
      "ETH Zurich", "Imperial College London", "Cambridge University", "Oxford University",
      "Tsinghua University", "National University of Singapore", "Nanyang Technological University",
      "EPFL", "Delft University of Technology", "Technical University of Munich",
      "University of Texas at Austin", "Purdue University"
    ]
  },
  {
    id: "med_schools_top_20",
    name: "Medical Schools Top 20",
    description: "Top medical schools globally",
    universities: [
      "Harvard Medical School", "Johns Hopkins School of Medicine", "Stanford Medicine",
      "UCSF School of Medicine", "University of Pennsylvania Perelman School of Medicine",
      "Columbia Vagelos College of Physicians and Surgeons", "Duke University School of Medicine",
      "Yale School of Medicine", "Washington University School of Medicine in St. Louis",
      "UCLA David Geffen School of Medicine", "University of Michigan Medical School",
      "NYU Grossman School of Medicine", "Northwestern Feinberg School of Medicine",
      "Cornell Weill Cornell Medicine", "University of Chicago Pritzker School of Medicine",
      "Oxford Medical School", "Cambridge School of Clinical Medicine", "Imperial College School of Medicine",
      "Karolinska Institute", "University of Toronto Faculty of Medicine"
    ]
  },
  {
    id: "law_schools_top_20",
    name: "Law Schools Top 20",
    description: "Top law schools in the US",
    universities: [
      "Yale Law School", "Stanford Law School", "Harvard Law School", "Columbia Law School",
      "University of Chicago Law School", "NYU School of Law", "University of Pennsylvania Carey Law School",
      "University of Virginia School of Law", "Northwestern Pritzker School of Law",
      "UC Berkeley School of Law", "Duke University School of Law", "University of Michigan Law School",
      "Cornell Law School", "Georgetown University Law Center", "UCLA School of Law",
      "University of Texas School of Law", "Vanderbilt Law School", "USC Gould School of Law",
      "Washington University School of Law", "University of Minnesota Law School"
    ]
  },
  {
    id: "design_schools",
    name: "Design Schools",
    description: "Top design and art schools",
    universities: [
      "Rhode Island School of Design", "Parsons School of Design", "Pratt Institute",
      "Art Center College of Design", "California College of the Arts", "School of Visual Arts",
      "Cooper Union", "Cranbrook Academy of Art", "Yale School of Art",
      "Royal College of Art", "Central Saint Martins", "Goldsmiths University of London",
      "Design Academy Eindhoven", "Politecnico di Milano", "Domus Academy",
      "Savannah College of Art and Design", "Maryland Institute College of Art",
      "School of the Art Institute of Chicago", "Carnegie Mellon School of Design",
      "Stanford d.school"
    ]
  },
  {
    id: "hospitality_schools",
    name: "Hospitality Schools",
    description: "Top hospitality and hotel management schools",
    universities: [
      "École hôtelière de Lausanne", "Cornell School of Hotel Administration",
      "Les Roches Global Hospitality Education", "Glion Institute of Higher Education",
      "ESSEC Business School", "University of Nevada Las Vegas", "Penn State School of Hospitality Management",
      "University of Houston Conrad N. Hilton College", "Swiss Education Group",
      "Hong Kong Polytechnic University School of Hotel and Tourism Management"
    ]
  }
]

interface UniversityPresetsModalProps {
  isOpen: boolean
  onClose: () => void
  onSelectPreset: (universities: string[]) => void
  organizationPresets?: UniversityPreset[]
  onSavePreset?: (preset: { name: string; description: string; universities: string[] }) => void
}

export function UniversityPresetsModal({
  isOpen,
  onClose,
  onSelectPreset,
  organizationPresets = [],
  onSavePreset
}: UniversityPresetsModalProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [activeTab, setActiveTab] = useState<"organization" | "general" | "custom">("general")
  const [showSaveForm, setShowSaveForm] = useState(false)
  const [newPresetName, setNewPresetName] = useState("")
  const [newPresetDescription, setNewPresetDescription] = useState("")
  const [customPresets, setCustomPresets] = useState<UniversityPreset[]>([])

  useEffect(() => {
    if (isOpen) {
      try {
        const stored = localStorage.getItem('university_custom_presets')
        if (stored) {
          const parsed = JSON.parse(stored)
          const formatted = parsed
            .filter((p: { universities?: string[] }) => Array.isArray(p.universities) && p.universities.length > 0)
            .map((p: { id: string; name: string; universities: string[]; description?: string }) => ({
              id: p.id,
              name: p.name,
              description: p.description || `Custom preset with ${p.universities.length} universities`,
              universities: [...p.universities]
            }))
          setCustomPresets(formatted)
        }
      } catch (e) {
      }
    }
  }, [isOpen])

  const handleDeleteCustomPreset = (presetId: string) => {
    try {
      const stored = localStorage.getItem('university_custom_presets')
      if (stored) {
        const parsed = JSON.parse(stored)
        const filtered = parsed.filter((p: { id: string }) => p.id !== presetId)
        localStorage.setItem('university_custom_presets', JSON.stringify(filtered))
        setCustomPresets(prev => prev.filter(p => p.id !== presetId))
      }
    } catch (e) {
    }
  }

  if (!isOpen) return null

  const filteredGeneralPresets = GENERAL_PRESETS.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredOrgPresets = organizationPresets.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const filteredCustomPresets = customPresets.filter(
    preset => preset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
              preset.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleSavePreset = () => {
    if (onSavePreset && newPresetName.trim()) {
      onSavePreset({
        name: newPresetName.trim(),
        description: newPresetDescription.trim(),
        universities: []
      })
      setNewPresetName("")
      setNewPresetDescription("")
      setShowSaveForm(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-[1px] z-overlay flex items-center justify-center p-4">
      <div className="bg-white rounded-md w-full max-w-2xl max-h-[80vh] flex flex-col dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <h2 className="text-base font-semibold lia-text-800 dark:text-lia-text-primary">University Presets</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-md transition-colors motion-reduce:transition-none"
          >
            <X className="w-5 h-5 lia-text-500" />
          </button>
        </div>

        <div className="px-4 py-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 lia-text-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search presets..."
              className="pl-9 text-sm"
            />
          </div>
        </div>

        <div className="flex border-b border-lia-border-subtle dark:border-lia-border-subtle">
          {customPresets.length > 0 && (
            <button
              onClick={() => setActiveTab("custom")}
              className={cn(
                "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
                activeTab === "custom"
                  ? "lia-text-900 dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle"
                  : "lia-text-500 hover:lia-text-700 dark:text-lia-text-tertiary dark:hover:lia-text-200"
              )}
            >
              Meus Presets ({customPresets.length})
            </button>
          )}
          <button
            onClick={() => setActiveTab("organization")}
            className={cn(
              "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "organization"
                ? "lia-text-900 dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle"
                : "lia-text-500 hover:lia-text-700 dark:text-lia-text-tertiary dark:hover:lia-text-200"
            )}
          >
            Organization Presets
          </button>
          <button
            onClick={() => setActiveTab("general")}
            className={cn(
              "flex-1 px-4 py-2.5 text-sm font-medium transition-colors",
              activeTab === "general"
                ? "lia-text-900 dark:text-lia-text-primary border-b-2 border-gray-900 dark:border-lia-border-subtle"
                : "lia-text-500 hover:lia-text-700 dark:text-lia-text-tertiary dark:hover:lia-text-200"
            )}
          >
            General Presets ({GENERAL_PRESETS.length})
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === "custom" ? (
            <div className="space-y-4">
              <p className="text-xs lia-text-500">
                Presets que você salvou
              </p>
              
              {filteredCustomPresets.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm lia-text-500">
                    Nenhum preset salvo encontrado
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredCustomPresets.map(preset => (
                    <div
                      key={preset.id}
                      className="w-full text-left p-3 rounded-md border border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50 dark:border-lia-border-default dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none group"
                    >
                      <div className="flex items-start justify-between">
                        <button
                          onClick={() => {
                            onSelectPreset(preset.universities)
                            onClose()
                          }}
                          className="flex-1 text-left"
                        >
                          <div className="font-medium text-sm lia-text-800">
                            {preset.name}
                          </div>
                          <div className="text-xs lia-text-500 mt-0.5">
                            {preset.description}
                          </div>
                        </button>
                        <div className="flex items-center gap-2">
                          <Badge className="text-micro bg-gray-100 lia-text-600">
                            {preset.universities.length} universities
                          </Badge>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteCustomPreset(preset.id)
                            }}
                            className="p-1 opacity-0 group-hover:opacity-100 hover:bg-status-error/10 rounded-md transition-colors motion-reduce:transition-none"
                            title="Excluir preset"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-status-error" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : activeTab === "organization" ? (
            <div className="space-y-4">
              <p className="text-xs lia-text-500">
                Presets created by you and your team members
              </p>
              
              {filteredOrgPresets.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm lia-text-500 mb-4">
                    No presets found, please create a new preset
                  </p>
                  <Button
                    onClick={() => setShowSaveForm(true)}
                    className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200 gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    Create New Preset
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredOrgPresets.map(preset => (
                    <button
                      key={preset.id}
                      onClick={() => {
                        onSelectPreset(preset.universities)
                        onClose()
                      }}
                      className="w-full text-left p-3 rounded-md border border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50 dark:border-lia-border-default dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium text-sm lia-text-800">
                            {preset.name}
                          </div>
                          <div className="text-xs lia-text-500 mt-0.5">
                            {preset.description}
                          </div>
                        </div>
                        <Badge className="text-micro bg-gray-100 lia-text-600">
                          {preset.universities.length} universities
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {showSaveForm && (
                <div className="mt-4 p-4 border border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
                  <h3 className="text-sm font-medium lia-text-800 mb-3">Save as Preset</h3>
                  <div className="space-y-3">
                    <div>
                      <Label className="text-xs">Preset Name</Label>
                      <Input
                        value={newPresetName}
                        onChange={(e) => setNewPresetName(e.target.value)}
                        placeholder="My University Preset"
                        className="mt-1"
                      />
                    </div>
                    <div>
                      <Label className="text-xs">Description</Label>
                      <Input
                        value={newPresetDescription}
                        onChange={(e) => setNewPresetDescription(e.target.value)}
                        placeholder="Description of this preset..."
                        className="mt-1"
                      />
                    </div>
                    <div className="flex gap-2 justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowSaveForm(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSavePreset}
                        disabled={!newPresetName.trim()}
                        className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-50 dark:lia-text-900 dark:hover:bg-gray-200"
                      >
                        Save Preset
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-xs lia-text-500">
                Curated university presets based on rankings and categories
              </p>
              
              <div className="space-y-2">
                {filteredGeneralPresets.map(preset => (
                  <button
                    key={preset.id}
                    onClick={() => {
                      onSelectPreset(preset.universities)
                      onClose()
                    }}
                    className="w-full text-left p-3 rounded-md border border-lia-border-subtle hover:border-gray-400 hover:bg-gray-50 dark:border-lia-border-default dark:hover:border-gray-500 dark:hover:bg-gray-700 transition-colors motion-reduce:transition-none"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm lia-text-800">
                            {preset.name}
                          </span>
                          <span className="text-xs lia-text-400">
                            ({preset.universities.slice(0, 2).join(', ')}, +{preset.universities.length - 2} universities)
                          </span>
                        </div>
                        <div className="text-xs lia-text-500 mt-0.5 line-clamp-1">
                          {preset.description}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default UniversityPresetsModal
