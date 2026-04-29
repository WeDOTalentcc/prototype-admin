# frozen_string_literal: true

require 'rails_helper'

RSpec.describe TagReplacer::Resolvers do
  let(:registry_tag) { TagReplacer::Registry::TagDefinition }

  describe TagReplacer::Resolvers::AttributeResolver do
    subject(:resolver) { described_class.new }

    let(:candidate) { double("Candidate", name: "Maria Silva", email: "maria@test.com") }
    let(:context) { instance_double(TagReplacer::Context) }

    it 'resolves an attribute from the entity' do
      tag = registry_tag.new(tag: "{{candidate_name}}", entity: :candidate, attribute: :name, resolver_type: :attribute, description: "", extra: {})
      allow(context).to receive(:fetch).with(:candidate).and_return(candidate)

      expect(resolver.resolve(context, tag)).to eq("Maria Silva")
    end

    it 'returns "-" when entity is nil' do
      tag = registry_tag.new(tag: "{{candidate_name}}", entity: :candidate, attribute: :name, resolver_type: :attribute, description: "", extra: {})
      allow(context).to receive(:fetch).with(:candidate).and_return(nil)

      expect(resolver.resolve(context, tag)).to eq("-")
    end

    it 'raises ResolutionError when attribute is not found on entity' do
      tag = registry_tag.new(tag: "{{candidate_nonexistent}}", entity: :candidate, attribute: :nonexistent, resolver_type: :attribute, description: "", extra: {})
      allow(context).to receive(:fetch).with(:candidate).and_return(candidate)

      expect { resolver.resolve(context, tag) }.to raise_error(TagReplacer::ResolutionError)
    end

    it 'returns "-" for nil attribute value' do
      entity = double("Entity", name: nil)
      tag = registry_tag.new(tag: "{{candidate_name}}", entity: :candidate, attribute: :name, resolver_type: :attribute, description: "", extra: {})
      allow(context).to receive(:fetch).with(:candidate).and_return(entity)

      expect(resolver.resolve(context, tag)).to eq("-")
    end
  end

  describe TagReplacer::Resolvers::DateResolver do
    subject(:resolver) { described_class.new }

    let(:context) { instance_double(TagReplacer::Context) }

    it 'returns BR formatted date for :br format' do
      tag = registry_tag.new(tag: "{{date_br_today}}", entity: nil, attribute: nil, resolver_type: :date, description: "", extra: { format: :br })
      travel_to Date.new(2026, 2, 27) do
        result = resolver.resolve(context, tag)
        expect(result).to include("2026")
      end
    end

    it 'returns EN formatted date for :en format' do
      tag = registry_tag.new(tag: "{{date_today}}", entity: nil, attribute: nil, resolver_type: :date, description: "", extra: { format: :en })
      travel_to Date.new(2026, 2, 27) do
        result = resolver.resolve(context, tag)
        expect(result).to include("2026")
      end
    end

    it 'returns ISO string for unknown format' do
      tag = registry_tag.new(tag: "{{date_today}}", entity: nil, attribute: nil, resolver_type: :date, description: "", extra: { format: :unknown })
      travel_to Date.new(2026, 2, 27) do
        expect(resolver.resolve(context, tag)).to eq("2026-02-27")
      end
    end
  end

  describe TagReplacer::Resolvers::MethodResolver do
    subject(:resolver) { described_class.new }

    let(:context) { instance_double(TagReplacer::Context) }

    it 'raises InvalidMethodError for disallowed methods' do
      tag = registry_tag.new(tag: "{{x}}", entity: :candidate, attribute: nil, resolver_type: :method, description: "", extra: { method_name: :destroy })
      allow(context).to receive(:fetch).with(:candidate).and_return(double("Candidate"))

      expect { resolver.resolve(context, tag) }.to raise_error(TagReplacer::InvalidMethodError)
    end

    it 'returns "-" when entity is nil' do
      tag = registry_tag.new(tag: "{{x}}", entity: :candidate, attribute: nil, resolver_type: :method, description: "", extra: { method_name: :name })
      allow(context).to receive(:fetch).with(:candidate).and_return(nil)

      expect(resolver.resolve(context, tag)).to eq("-")
    end

    it 'raises ResolutionError when entity does not respond to the method' do
      tag = registry_tag.new(tag: "{{x}}", entity: :candidate, attribute: nil, resolver_type: :method, description: "", extra: { method_name: :name })
      allow(context).to receive(:fetch).with(:candidate).and_return(double("NoName"))

      expect { resolver.resolve(context, tag) }.to raise_error(TagReplacer::ResolutionError)
    end
  end

  describe TagReplacer::ResolverFactory do
    it 'returns AttributeResolver for :attribute type' do
      tag = registry_tag.new(tag: "{{x}}", entity: :candidate, attribute: :name, resolver_type: :attribute, description: "", extra: {})
      expect(TagReplacer::ResolverFactory.for(tag)).to be_a(TagReplacer::Resolvers::AttributeResolver)
    end

    it 'returns DateResolver for :date type' do
      tag = registry_tag.new(tag: "{{x}}", entity: nil, attribute: nil, resolver_type: :date, description: "", extra: {})
      expect(TagReplacer::ResolverFactory.for(tag)).to be_a(TagReplacer::Resolvers::DateResolver)
    end

    it 'returns UrlResolver for :url type' do
      tag = registry_tag.new(tag: "{{x}}", entity: :candidate, attribute: nil, resolver_type: :url, description: "", extra: { url_type: :candidate_access })
      expect(TagReplacer::ResolverFactory.for(tag)).to be_a(TagReplacer::Resolvers::UrlResolver)
    end

    it 'returns MethodResolver for :method type' do
      tag = registry_tag.new(tag: "{{x}}", entity: :candidate, attribute: nil, resolver_type: :method, description: "", extra: { method_name: :name })
      expect(TagReplacer::ResolverFactory.for(tag)).to be_a(TagReplacer::Resolvers::MethodResolver)
    end

    it 'raises ResolutionError for unknown resolver type' do
      tag = registry_tag.new(tag: "{{x}}", entity: nil, attribute: nil, resolver_type: :unknown, description: "", extra: {})
      expect { TagReplacer::ResolverFactory.for(tag) }.to raise_error(TagReplacer::ResolutionError)
    end
  end
end
