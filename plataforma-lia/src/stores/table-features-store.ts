import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface SortState {
  field: string | null
  order: 'asc' | 'desc'
}

interface TableFeaturesState {
  tableWidths: Record<string, Record<string, number>>
  tableOrders: Record<string, string[]>
  tableSorts: Record<string, SortState>
}

interface TableFeaturesActions {
  setTableWidths: (tableId: string, widths: Record<string, number>) => void
  setTableOrder: (tableId: string, order: string[]) => void
  setTableSort: (tableId: string, sort: SortState) => void
  getTableWidths: (tableId: string) => Record<string, number> | null
  getTableOrder: (tableId: string) => string[] | null
  getTableSort: (tableId: string) => SortState | null
  removeTableWidths: (tableId: string) => void
  removeTableOrder: (tableId: string) => void
}

export type TableFeaturesStore = TableFeaturesState & TableFeaturesActions

export const useTableFeaturesStore = create<TableFeaturesStore>()(
  devtools(
    persist(
      (set, get) => ({
        tableWidths: {},
        tableOrders: {},
        tableSorts: {},

        setTableWidths: (tableId, widths) =>
          set(
            (state) => ({
              tableWidths: { ...state.tableWidths, [tableId]: widths },
            }),
            false,
            'tableFeatures/setTableWidths'
          ),

        setTableOrder: (tableId, order) =>
          set(
            (state) => ({
              tableOrders: { ...state.tableOrders, [tableId]: order },
            }),
            false,
            'tableFeatures/setTableOrder'
          ),

        setTableSort: (tableId, sort) =>
          set(
            (state) => ({
              tableSorts: { ...state.tableSorts, [tableId]: sort },
            }),
            false,
            'tableFeatures/setTableSort'
          ),

        getTableWidths: (tableId) => {
          return get().tableWidths[tableId] ?? null
        },

        getTableOrder: (tableId) => {
          return get().tableOrders[tableId] ?? null
        },

        getTableSort: (tableId) => {
          return get().tableSorts[tableId] ?? null
        },

        removeTableWidths: (tableId) =>
          set(
            (state) => {
              const updated = { ...state.tableWidths }
              delete updated[tableId]
              return { tableWidths: updated }
            },
            false,
            'tableFeatures/removeTableWidths'
          ),

        removeTableOrder: (tableId) =>
          set(
            (state) => {
              const updated = { ...state.tableOrders }
              delete updated[tableId]
              return { tableOrders: updated }
            },
            false,
            'tableFeatures/removeTableOrder'
          ),
      }),
      {
        name: 'lia-table-features-store',
        partialize: (state) => ({
          tableWidths: state.tableWidths,
          tableOrders: state.tableOrders,
          tableSorts: state.tableSorts,
        }),
      }
    ),
    { name: 'TableFeaturesStore' }
  )
)
