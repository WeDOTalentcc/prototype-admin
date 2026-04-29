# frozen_string_literal: true

RSpec.configure do |config|
  config.before do
    allow(Wsi::ReportGenerationJob).to receive(:perform_async).and_return("jid")
  end
end
