# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::Constants do
  describe "SENIORITY_KEY_MAP" do
    it "maps Job::SENIORITY indices 0-7 to semantic WSI keys" do
      expect(described_class::SENIORITY_KEY_MAP[0]).to eq("junior")
      expect(described_class::SENIORITY_KEY_MAP[1]).to eq("pleno")
      expect(described_class::SENIORITY_KEY_MAP[2]).to eq("senior")
      expect(described_class::SENIORITY_KEY_MAP[3]).to eq("principal")
      expect(described_class::SENIORITY_KEY_MAP[4]).to eq("estagiario")
      expect(described_class::SENIORITY_KEY_MAP[5]).to eq("lead")
      expect(described_class::SENIORITY_KEY_MAP[6]).to eq("manager")
      expect(described_class::SENIORITY_KEY_MAP[7]).to eq("diretor")
    end

    it "has exactly eight entries aligned with Job::SENIORITY" do
      expect(described_class::SENIORITY_KEY_MAP.size).to eq(Job::SENIORITY.size)
    end
  end

  describe ".seniority_key" do
    it "returns nil when job is nil" do
      expect(described_class.seniority_key(nil)).to be_nil
    end

    it "returns pleno when seniority is nil" do
      job = instance_double(Job, seniority: nil)
      expect(described_class.seniority_key(job)).to eq("pleno")
    end

    it "returns senior when seniority is 2 (Sênior)" do
      job = instance_double(Job, seniority: 2)
      expect(described_class.seniority_key(job)).to eq("senior")
    end

    it "returns pleno for unknown index" do
      job = instance_double(Job, seniority: 99)
      expect(described_class.seniority_key(job)).to eq("pleno")
    end

    (0..7).each do |idx|
      it "returns SENIORITY_KEY_MAP[#{idx}] for seniority #{idx}" do
        job = instance_double(Job, seniority: idx)
        expect(described_class.seniority_key(job)).to eq(described_class::SENIORITY_KEY_MAP[idx])
      end
    end
  end

  describe "QUESTION_DISTRIBUTIONS / .big_five_top_n" do
    it "covers methodology seniority keys plus manager and vp_clevel" do
      methodology = %w[estagiario junior pleno senior lead principal diretor vp_clevel manager]
      methodology.each do |key|
        expect(described_class::QUESTION_DISTRIBUTIONS[:compact]).to have_key(key)
        expect(described_class::QUESTION_DISTRIBUTIONS[:full]).to have_key(key)
      end
    end

    describe ".big_five_top_n" do
      it "matches methodology §5.4–5.5 top_n_traits" do
        expect(described_class.big_five_top_n("estagiario", :compact)).to eq(2)
        expect(described_class.big_five_top_n("pleno", :compact)).to eq(2)
        expect(described_class.big_five_top_n("senior", :compact)).to eq(3)
        expect(described_class.big_five_top_n("lead", :compact)).to eq(4)
        expect(described_class.big_five_top_n("vp_clevel", :compact)).to eq(5)

        expect(described_class.big_five_top_n("estagiario", :full)).to eq(3)
        expect(described_class.big_five_top_n("junior", :full)).to eq(3)
        expect(described_class.big_five_top_n("pleno", :full)).to eq(4)
        expect(described_class.big_five_top_n("senior", :full)).to eq(5)
        expect(described_class.big_five_top_n("diretor", :full)).to eq(5)
        expect(described_class.big_five_top_n("vp_clevel", :full)).to eq(5)
      end

      it "falls back to pleno when seniority_key is unknown" do
        expect(described_class.big_five_top_n("unknown_level", :compact)).to eq(2)
        expect(described_class.big_five_top_n("unknown_level", :full)).to eq(4)
      end

      it "raises ArgumentError for invalid mode" do
        expect { described_class.big_five_top_n("senior", :wide) }.to raise_error(ArgumentError, /mode must be :compact or :full/)
      end

      [
        { key: "estagiario", compact: 2, full: 3 },
        { key: "junior", compact: 2, full: 3 },
        { key: "pleno", compact: 2, full: 4 },
        { key: "senior", compact: 3, full: 5 },
        { key: "principal", compact: 3, full: 5 },
        { key: "lead", compact: 4, full: 5 },
        { key: "manager", compact: 4, full: 5 },
        { key: "diretor", compact: 4, full: 5 },
        { key: "vp_clevel", compact: 5, full: 5 }
      ].each do |row|
        it "returns compact #{row[:compact]} and full #{row[:full]} for #{row[:key]}" do
          expect(described_class.big_five_top_n(row[:key], :compact)).to eq(row[:compact])
          expect(described_class.big_five_top_n(row[:key], :full)).to eq(row[:full])
        end
      end

      it "accepts string mode" do
        expect(described_class.big_five_top_n("junior", "compact")).to eq(2)
        expect(described_class.big_five_top_n("junior", "full")).to eq(3)
      end
    end
  end

  describe "SENIORITY_WEIGHTS" do
    it "matches methodology §5.6 (technical / behavioral normalized)" do
      expect(described_class::SENIORITY_WEIGHTS["senior"]).to include(technical: 0.5625, behavioral: 0.4375)
      expect(described_class::SENIORITY_WEIGHTS["lead"]).to include(technical: 0.4375, behavioral: 0.5625)
    end
  end

  describe "SENIORITY_CALIBRATION" do
    it "matches methodology §4.1 (Bloom / Dreyfus by seniority)" do
      expect(described_class::SENIORITY_CALIBRATION["estagiario"]).to include(
        experience_years: "0-1",
        dreyfus_technical_level: 1,
        dreyfus_technical_label: "Novice",
        bloom_expected: "1-2",
        dreyfus_behavioral_level: 1
      )
      expect(described_class::SENIORITY_CALIBRATION["junior"]).to include(
        experience_years: "1-3",
        dreyfus_technical_level: 2,
        bloom_expected: "2-3",
        dreyfus_behavioral_level: 2
      )
      expect(described_class::SENIORITY_CALIBRATION["pleno"]).to include(
        experience_years: "3-6",
        dreyfus_technical_level: 3,
        dreyfus_technical_label: "Competent",
        bloom_expected: "4",
        dreyfus_behavioral_level: 3
      )
      expect(described_class::SENIORITY_CALIBRATION["senior"]).to include(
        experience_years: "6-10",
        dreyfus_technical_level: 4,
        bloom_expected: "5",
        dreyfus_behavioral_level: 4
      )
      expect(described_class::SENIORITY_CALIBRATION["lead"]).to include(
        experience_years: "8-15",
        dreyfus_technical_level: 5,
        bloom_expected: "6",
        dreyfus_behavioral_level: 5
      )
      expect(described_class::SENIORITY_CALIBRATION["diretor"]).to include(
        experience_years: "10-20",
        dreyfus_technical_level: 5,
        bloom_expected: "6"
      )
      expect(described_class::SENIORITY_CALIBRATION["vp_clevel"]).to include(
        experience_years: "15+",
        dreyfus_technical_level: 5,
        bloom_expected: "6"
      )
    end

    describe ".seniority_calibration" do
      it "falls back to pleno for unknown keys" do
        expect(described_class.seniority_calibration("unknown")).to eq(described_class::SENIORITY_CALIBRATION["pleno"])
      end
    end
  end
end
