require "rails_helper"

RSpec.describe OrganizationalStructureBuilderService, type: :service do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }

  describe "#build" do
    let(:payload) do
      {
        department: {
          name: "Tecnologia"
        },
        hiring_manager: {
          name: user.name,
          email: user.email,
          title: "Gerente de Engenharia"
        },
        team: {
          name: "Produto",
          size: 5,
          composition: [
            { role: "Backend", count: 3 },
            { role: "Frontend", count: 2 }
          ]
        },
        reports_to: {
          position: "Diretor de Tecnologia"
        }
      }
    end

    it "builds structure data and updates job" do
      result = described_class.new(job, payload).build

      expect(result[:success]).to be true
      expect(result[:structure][:department]).to eq("Tecnologia")
      expect(job.reload.department.name).to eq("Tecnologia")
      expect(job.team).to be_present
      expect(job.hiring_manager).to eq(user)
      expect(job.reports_to_position).to be_present
      expect(job.team_composition.size).to eq(2)
      expect(result[:changes]).to include("Departamento definido: Tecnologia")
    end

    it "returns errors when manager is missing" do
      payload[:hiring_manager][:email] = nil
      payload[:hiring_manager][:name] = "Unknown"

      result = described_class.new(job, payload).build

      expect(result[:success]).to be false
      expect(result[:errors]).to include("Gestor Unknown não encontrado")
    end
  end
end
