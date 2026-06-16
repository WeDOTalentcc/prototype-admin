require 'rails_helper'

RSpec.describe Sector, type: :model do
  subject { build(:sector) }

  # Validações
  describe 'validations' do
    it { should validate_presence_of(:name) }
    it { should validate_presence_of(:level) }
    it { should validate_numericality_of(:level).only_integer.is_greater_than_or_equal_to(0) }

    it 'is valid with valid attributes' do
      expect(subject).to be_valid
    end

    context 'validate_parent_level' do
      let(:parent) { create(:sector, level: 0) }
      let(:child) { build(:sector, parent_sector: parent, level: 1) }

      it 'is valid when parent level is less than child level' do
        expect(child).to be_valid
      end

      it 'is invalid when parent level is greater than or equal to child level' do
        invalid_child = build(:sector, parent_sector: parent, level: 0)
        expect(invalid_child).not_to be_valid
        expect(invalid_child.errors[:parent_sector]).to include("deve ter um nível inferior ao nível atual")
      end
    end

    context 'validate_public_sector_has_no_account' do
      it 'is invalid when public sector has account_id' do
        account = create(:account)
        sector = build(:sector, is_public: true, account_id: account.id)
        expect(sector).not_to be_valid
        expect(sector.errors[:account_id]).to include("setores públicos não podem ter account_id")
      end

      it 'is invalid when private sector has no account_id' do
        sector = build(:sector, is_public: false, account_id: nil)
        expect(sector).not_to be_valid
        expect(sector.errors[:account_id]).to include("setores privados devem ter account_id")
      end

      it 'is valid when public sector has no account_id' do
        sector = build(:sector, is_public: true, account_id: nil)
        expect(sector).to be_valid
      end

      it 'is valid when private sector has account_id' do
        account = create(:account)
        sector = build(:sector, is_public: false, account_id: account.id)
        expect(sector).to be_valid
      end
    end
  end

  # Relacionamentos
  describe 'associations' do
    it { should belong_to(:parent_sector).optional }
    it { should belong_to(:account).optional }
    it { should have_many(:child_sectors).dependent(:destroy) }
  end

  # Scopes
  describe 'scopes' do
    let!(:active_sector) { create(:sector, is_deleted: false) }
    let!(:deleted_sector) { create(:sector, is_deleted: true) }
    let!(:public_sector) { create(:sector, is_public: true, account_id: nil) }
    let!(:account) { create(:account) }
    let!(:private_sector) { create(:sector, is_public: false, account_id: account.id) }
    let!(:parent) { create(:sector, level: 0) }
    let!(:child) { create(:sector, parent_sector: parent, level: 1) }

    it '.active returns only active sectors' do
      expect(Sector.active).to include(active_sector)
      expect(Sector.active).not_to include(deleted_sector)
    end

    it '.public_sectors returns only public sectors without account' do
      expect(Sector.public_sectors).to include(public_sector)
      expect(Sector.public_sectors).not_to include(private_sector)
    end

    it '.for_account returns sectors for specific account' do
      expect(Sector.for_account(account.id)).to include(private_sector)
      expect(Sector.for_account(account.id)).not_to include(public_sector)
    end

    it '.root_sectors returns only root sectors' do
      expect(Sector.root_sectors).to include(parent)
      expect(Sector.root_sectors).not_to include(child)
    end

    it '.by_level returns sectors at specific level' do
      expect(Sector.by_level(0)).to include(parent)
      expect(Sector.by_level(1)).to include(child)
    end
  end

  # Callbacks
  describe 'callbacks' do
    describe 'before_validation :set_level' do
      it 'sets level to 0 for root sectors' do
        sector = build(:sector, parent_sector: nil, level: nil)
        sector.valid?
        expect(sector.level).to eq(0)
      end

      it 'sets level to parent level + 1 for child sectors' do
        parent = create(:sector, level: 0)
        child = build(:sector, parent_sector: parent, level: nil)
        child.valid?
        expect(child.level).to eq(1)
      end
    end

    describe 'before_destroy :check_has_children' do
      it 'prevents deletion when sector has children' do
        parent = create(:sector, level: 0)
        create(:sector, parent_sector: parent, level: 1)

        expect { parent.destroy }.not_to change(Sector, :count)
        expect(parent.errors[:base]).to include("Não é possível excluir um setor que possui subsetores")
      end

      it 'allows deletion when sector has no children' do
        sector = create(:sector)
        expect { sector.destroy }.to change(Sector, :count).by(-1)
      end
    end
  end

  # Métodos de instância
  describe 'instance methods' do
    describe '#has_children?' do
      it 'returns true when sector has children' do
        parent = create(:sector)
        create(:sector, parent_sector: parent)
        expect(parent.has_children?).to be true
      end

      it 'returns false when sector has no children' do
        sector = create(:sector)
        expect(sector.has_children?).to be false
      end
    end

    describe '#children_count' do
      it 'returns the count of child sectors' do
        parent = create(:sector)
        create_list(:sector, 3, parent_sector: parent)
        expect(parent.children_count).to eq(3)
      end
    end

    describe '#full_path' do
      it 'returns just the name for root sectors' do
        sector = create(:sector, name: "Technology")
        expect(sector.full_path).to eq("Technology")
      end

      it 'returns full hierarchical path for nested sectors' do
        grandparent = create(:sector, name: "Technology", level: 0)
        parent = create(:sector, name: "Software", parent_sector: grandparent, level: 1)
        child = create(:sector, name: "SaaS", parent_sector: parent, level: 2)

        expect(child.full_path).to eq("Technology > Software > SaaS")
      end
    end

    describe '#ancestors' do
      it 'returns empty array for root sectors' do
        sector = create(:sector)
        expect(sector.ancestors).to eq([])
      end

      it 'returns all ancestors in order' do
        grandparent = create(:sector, level: 0)
        parent = create(:sector, parent_sector: grandparent, level: 1)
        child = create(:sector, parent_sector: parent, level: 2)

        expect(child.ancestors).to eq([ parent, grandparent ])
      end
    end

    describe '#descendants' do
      it 'returns all descendants recursively' do
        parent = create(:sector, level: 0)
        child1 = create(:sector, parent_sector: parent, level: 1)
        child2 = create(:sector, parent_sector: parent, level: 1)
        grandchild = create(:sector, parent_sector: child1, level: 2)

        descendants = parent.descendants
        expect(descendants).to include(child1, child2, grandchild)
        expect(descendants.size).to eq(3)
      end
    end

    describe '#siblings' do
      it 'returns other sectors with the same parent' do
        parent = create(:sector)
        child1 = create(:sector, parent_sector: parent)
        child2 = create(:sector, parent_sector: parent)
        child3 = create(:sector, parent_sector: parent)

        expect(child1.siblings).to contain_exactly(child2, child3)
      end

      it 'returns empty relation for root sectors' do
        sector = create(:sector)
        expect(sector.siblings).to be_empty
      end
    end
  end

  # Searchkick
  describe 'searchkick' do
    it 'includes Searchable concern' do
      expect(Sector.ancestors).to include(Searchable)
    end

    it 'defines search_data method' do
      sector = create(:sector, name: "Tech", tags: [ "B2B", "SaaS" ])
      data = sector.search_data

      expect(data[:name]).to eq("Tech")
      expect(data[:tags]).to eq([ "B2B", "SaaS" ])
      expect(data).to have_key(:level)
      expect(data).to have_key(:is_public)
    end
  end
end
