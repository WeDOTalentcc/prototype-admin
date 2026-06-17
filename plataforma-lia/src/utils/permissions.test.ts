import { describe, it, expect, beforeEach } from "vitest"
import { permissionManager, setCurrentUser, LIA_ACTIONS_BY_ROLE, type User } from "./permissions"

const adminUser: User = {
  id: "1",
  name: "Admin User",
  email: "admin@test.com",
  role: "admin",
  company: "TestCo",
}

const internUser: User = {
  id: "2",
  name: "Intern User",
  email: "intern@test.com",
  role: "intern",
  company: "TestCo",
}

const recruiterUser: User = {
  id: "3",
  name: "Recruiter",
  email: "recruiter@test.com",
  role: "recruiter",
  company: "TestCo",
}

const managerUser: User = {
  id: "4",
  name: "Manager",
  email: "manager@test.com",
  role: "manager",
  company: "TestCo",
}

beforeEach(() => {
  permissionManager.setUser(null as never)
})

describe("permissionManager.hasPermission", () => {
  it("returns false when no user is set", () => {
    expect(permissionManager.hasPermission("read", "candidates")).toBe(false)
  })

  it("admin has permission for anything", () => {
    setCurrentUser(adminUser)
    expect(permissionManager.hasPermission("read", "candidates")).toBe(true)
    expect(permissionManager.hasPermission("delete", "jobs")).toBe(true)
    expect(permissionManager.hasPermission("execute", "anything")).toBe(true)
  })

  it("intern can only read candidates (with conditions)", () => {
    setCurrentUser(internUser)
    expect(permissionManager.hasPermission("read", "candidates")).toBe(true)
    expect(permissionManager.hasPermission("write", "candidates")).toBe(false)
    expect(permissionManager.hasPermission("delete", "candidates")).toBe(false)
  })

  it("manager can write candidates and jobs", () => {
    setCurrentUser(managerUser)
    expect(permissionManager.hasPermission("write", "candidates")).toBe(true)
    expect(permissionManager.hasPermission("write", "jobs")).toBe(true)
  })
})

describe("permissionManager.canUseLiaAction", () => {
  it("returns false when no user is set", () => {
    expect(permissionManager.canUseLiaAction("fazer_triagem")).toBe(false)
  })

  it("admin can use all LIA actions", () => {
    setCurrentUser(adminUser)
    expect(permissionManager.canUseLiaAction("fazer_triagem")).toBe(true)
    expect(permissionManager.canUseLiaAction("sugestao_oferta")).toBe(true)
    expect(permissionManager.canUseLiaAction("criar_alerta")).toBe(true)
  })

  it("intern can only use basic LIA actions", () => {
    setCurrentUser(internUser)
    expect(permissionManager.canUseLiaAction("coletar_dados")).toBe(true)
    expect(permissionManager.canUseLiaAction("identificar_pendencias")).toBe(true)
    expect(permissionManager.canUseLiaAction("fazer_triagem")).toBe(false)
    expect(permissionManager.canUseLiaAction("sugestao_oferta")).toBe(false)
  })
})

describe("permissionManager.canManageUser", () => {
  it("returns false when no user is set", () => {
    expect(permissionManager.canManageUser(internUser)).toBe(false)
  })

  it("admin can manage all roles", () => {
    setCurrentUser(adminUser)
    expect(permissionManager.canManageUser(internUser)).toBe(true)
    expect(permissionManager.canManageUser(managerUser)).toBe(true)
  })

  it("intern cannot manage anyone", () => {
    setCurrentUser(internUser)
    expect(permissionManager.canManageUser(recruiterUser)).toBe(false)
    expect(permissionManager.canManageUser(managerUser)).toBe(false)
  })
})

describe("permissionManager.getRoleLabel", () => {
  it("returns 'Usuário' when no user is set", () => {
    expect(permissionManager.getRoleLabel()).toBe("Usuário")
  })

  it("returns 'Administrador' for admin role", () => {
    setCurrentUser(adminUser)
    expect(permissionManager.getRoleLabel()).toBe("Administrador")
  })

  it("returns 'Estagiário' for intern role", () => {
    setCurrentUser(internUser)
    expect(permissionManager.getRoleLabel()).toBe("Estagiário")
  })
})

describe("LIA_ACTIONS_BY_ROLE", () => {
  it("admin has more actions than intern", () => {
    expect(LIA_ACTIONS_BY_ROLE.admin.length).toBeGreaterThan(LIA_ACTIONS_BY_ROLE.intern.length)
  })

  it("intern actions are a subset of admin actions", () => {
    for (const action of LIA_ACTIONS_BY_ROLE.intern) {
      expect(LIA_ACTIONS_BY_ROLE.admin).toContain(action)
    }
  })
})
