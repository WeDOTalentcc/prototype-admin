---
applyTo: "spec/**/*.rb"
---

# RSpec Tests — WeDO Talent ATS

## Directory Structure

```
spec/
├── factories/          # FactoryBot factories
├── models/             # Model specs
├── services/           # Service specs
├── requests/           # Controller/integration specs
├── controllers/        # Legacy controller specs
├── serializer/         # Serializer specs
├── jobs/               # Sidekiq job specs
├── workers/            # Worker specs
├── validators/         # Custom validator specs
├── channels/           # ActionCable specs
├── support/            # Helpers (auth, tenant, etc.)
├── rails_helper.rb
└── spec_helper.rb
```

## Model Specs

```ruby
# frozen_string_literal: true

RSpec.describe Job, type: :model do
  describe "validations" do
    it { is_expected.to validate_presence_of(:title) }
    it { is_expected.to validate_uniqueness_of(:external_id).scoped_to(:account_id).allow_nil }
  end

  describe "associations" do
    it { is_expected.to have_many(:applies).dependent(:destroy) }
    it { is_expected.to have_many(:evaluations).dependent(:destroy) }
    it { is_expected.to have_many(:selective_processes).dependent(:destroy) }
    it { is_expected.to belong_to(:user).optional }
    it { is_expected.to belong_to(:account).optional }
    it { is_expected.to belong_to(:department).optional }
    it { is_expected.to have_one(:analytics_snapshot).dependent(:destroy) }
  end

  describe "enums" do
    it { is_expected.to define_enum_for(:employment_type).with_values(clt: 0, pj: 1, internship: 2) }
  end

  describe "scopes" do
    describe ".active" do
      let!(:active_job) { create(:job, is_active: true, is_deleted: false) }
      let!(:deleted_job) { create(:job, is_deleted: true) }
      let!(:inactive_job) { create(:job, is_active: false) }

      it "returns only active non-deleted jobs" do
        expect(Job.active).to contain_exactly(active_job)
      end
    end
  end

  describe "#soft_delete!" do
    let(:job) { create(:job) }

    it "sets is_deleted to true" do
      job.soft_delete!
      expect(job.reload.is_deleted).to be true
    end
  end
end
```

## Service Specs

```ruby
# frozen_string_literal: true

RSpec.describe Jobs::PublishService do
  subject(:result) { described_class.new(job: job).call }

  let(:account) { create(:account) }
  let(:job) { create(:job, account: account, is_active: false) }

  before { Apartment::Tenant.switch!(account.tenant) }

  context "when job is ready for publication" do
    before do
      allow_any_instance_of(Jobs::FieldRequirementChecker)
        .to receive(:is_ready_for_publication?).and_return(true)
      create(:job_status, name: "Ativa")
    end

    it "publishes the job" do
      expect(result[:success]).to be true
    end

    it "sets published_date" do
      result
      expect(job.reload.published_date).to be_present
    end

    it "activates the job" do
      result
      expect(job.reload.is_active).to be true
    end
  end

  context "when job is not ready" do
    before do
      allow_any_instance_of(Jobs::FieldRequirementChecker)
        .to receive(:is_ready_for_publication?).and_return(false)
      allow_any_instance_of(Jobs::FieldRequirementChecker)
        .to receive(:make_missing_fields).and_return([:title])
    end

    it "returns error" do
      expect(result[:success]).to be false
      expect(result[:error]).to be_present
    end

    it "includes missing fields" do
      expect(result[:missing_fields]).to include(:title)
    end
  end
end
```

## Request Specs (Controllers)

```ruby
# frozen_string_literal: true

RSpec.describe "V1::Users::Jobs", type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers_for(user) }

  before { Apartment::Tenant.switch!(account.tenant) }

  describe "GET /v1/users/jobs" do
    before { create_list(:job, 3, user: user, account: account) }

    it "returns paginated jobs" do
      get "/v1/users/jobs", headers: headers
      expect(response).to have_http_status(:ok)
      expect(json_response["data"].size).to eq(3)
      expect(json_response["meta"]["total"]).to eq(3)
    end

    it "filters by is_active" do
      get "/v1/users/jobs", headers: headers, params: { where: { is_active: true }.to_json }
      expect(response).to have_http_status(:ok)
    end
  end

  describe "POST /v1/users/jobs" do
    let(:valid_params) { { job: attributes_for(:job) } }

    it "creates a job" do
      expect {
        post "/v1/users/jobs", headers: headers, params: valid_params
      }.to change(Job, :count).by(1)
      expect(response).to have_http_status(:created)
    end

    context "with invalid params" do
      let(:invalid_params) { { job: { title: nil } } }

      it "returns unprocessable entity" do
        post "/v1/users/jobs", headers: headers, params: invalid_params
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe "PUT /v1/users/jobs/:id" do
    let(:job) { create(:job, user: user, account: account) }

    it "updates the job" do
      put "/v1/users/jobs/#{job.id}", headers: headers, params: { job: { title: "Updated" } }
      expect(response).to have_http_status(:ok)
      expect(job.reload.title).to eq("Updated")
    end
  end
end
```

## Job Specs (Sidekiq)

```ruby
# frozen_string_literal: true

RSpec.describe Jobs::RefreshAnalyticsJob, type: :job do
  let(:account) { create(:account) }
  let(:job) { create(:job, account: account) }

  before { Apartment::Tenant.switch!(account.tenant) }

  it "calls AnalyticsService" do
    service = instance_double(Jobs::AnalyticsService)
    allow(Jobs::AnalyticsService).to receive(:new).and_return(service)
    allow(service).to receive(:call)

    described_class.new.perform(job.id, account.id)

    expect(service).to have_received(:call)
  end

  context "when job not found" do
    it "does not raise" do
      expect { described_class.new.perform(999_999, account.id) }.not_to raise_error
    end
  end
end
```

## Testing Patterns

### let vs let!

```ruby
let(:user) { create(:user) }              # Lazy — created when first referenced
let!(:required_record) { create(:job) }   # Eager — created before each test
```

### described_class

```ruby
subject(:service) { described_class.new(job: job) }
```

### Contexts

```ruby
context "when user is admin" do
  let(:user) { create(:user, is_admin: true) }
  # ...
end

context "with valid params" do
  # ...
end

context "when record not found" do
  # ...
end
```

### Doubles for Unit Tests

Prefer doubles over factories for pure unit tests:

```ruby
RSpec.describe Candidates::Search::WeightedRankFusion do
  describe "#combine" do
    it "combines rankings with RRF" do
      es_rankings = { 1 => 1, 2 => 2, 3 => 3 }
      emb_rankings = { 2 => 1, 3 => 2, 1 => 3 }

      result = described_class.combine(es_rankings, emb_rankings, es_weight: 0.7, emb_weight: 0.3)

      expect(result.keys.first).to eq(2)
    end
  end
end
```

### Multi-tenancy Setup

```ruby
let(:account) { create(:account) }
before { Apartment::Tenant.switch!(account.tenant) }
after { Apartment::Tenant.switch!("public") }
```

### Searchkick in Tests

Stub when not testing search:

```ruby
before { allow(Job).to receive(:search).and_return(mock_search_results) }
```

Or disable callbacks:

```ruby
before { Searchkick.disable_callbacks }
after { Searchkick.enable_callbacks }
```

### VCR for External APIs

```ruby
it "calls Gemini API", vcr: { cassette_name: "gemini/score_candidate" } do
  result = described_class.new(evaluation_candidate: ec).call
  expect(result[:score]).to be_present
end
```

## Rules

- `let` for setup, `let!` only when eager needed
- `described_class` to reference tested class
- `context "when ..."` for scenario grouping
- `build_stubbed` for unit, `create` for integration
- `shared_examples` for common behaviors (soft-delete, pagination, auth)
- Test multi-tenancy explicitly with `Apartment::Tenant.switch!`
- Stub Searchkick when not testing search
- Never test private methods directly
- Each model, service, and controller should have specs
